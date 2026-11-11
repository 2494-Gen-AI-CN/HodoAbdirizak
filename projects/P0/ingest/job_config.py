"""Configuration and source-file helpers for the ingestion job."""

from pathlib import Path
import re

import pandas as pd
import yaml


_TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_config(config_path):
    """Read and validate the ingestion YAML configuration."""
    config_path = Path(config_path)
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping.")

    bigquery_config = config.get("bigquery")
    if not isinstance(bigquery_config, dict):
        raise ValueError("Configuration must define a 'bigquery' mapping.")
    for key in ("project", "raw_dataset", "warehouse_dataset"):
        if not isinstance(bigquery_config.get(key), str) or not bigquery_config[key]:
            raise ValueError(f"Configuration must define bigquery.{key}.")
    for key in ("raw_dataset", "warehouse_dataset"):
        if not _TABLE_NAME.fullmatch(bigquery_config[key]):
            raise ValueError(f"bigquery.{key} must be a valid BigQuery dataset name.")

    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Configuration must define at least one source.")
    source_names = set()
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            raise ValueError(f"{label} must be a mapping.")
        name = source.get("name")
        if not isinstance(name, str) or not _TABLE_NAME.fullmatch(name):
            raise ValueError(f"{label}.name must be a valid BigQuery table name.")
        if name in source_names:
            raise ValueError(f"Duplicate source name: {name}")
        source_names.add(name)
        if not isinstance(source.get("file"), str) or not source["file"]:
            raise ValueError(f"{label}.file must name a source file.")
        if source.get("format") not in {"csv", "json"}:
            raise ValueError(f"{label}.format must be 'csv' or 'json'.")
        transform = source.get("transform")
        if transform not in {None, "ems_incidents"}:
            raise ValueError(
                f"{label}.transform must be omitted or 'ems_incidents'."
            )
        if transform == "ems_incidents":
            for key in ("clean_table", "reject_table"):
                table_name = source.get(key)
                if not isinstance(table_name, str) or not _TABLE_NAME.fullmatch(
                    table_name
                ):
                    raise ValueError(
                        f"{label}.{key} must be a valid BigQuery table name "
                        "when transform is 'ems_incidents'."
                    )

    return config


def load_source_dataframe(source_path, file_format):
    """Read CSV or newline-delimited JSON into string-valued columns."""
    source_path = Path(source_path)
    if file_format == "csv":
        return pd.read_csv(source_path, dtype=str)
    if file_format == "json":
        return pd.read_json(source_path, lines=True, dtype=False).astype("string")
    raise ValueError(f"Unsupported source format: {file_format}")
