"""Cleasing rules for cleaning the dataset."""

import pandas as pd

DATE_FORMAT = "%m/%d/%Y %I:%M:%S %p"

def add_typed_columns(df):
    """Return a copy with typed columns added. Bad values become NaN/NaT."""
    out = df.copy()
    for src, dst in [
        ("DISPATCH_RESPONSE_SECONDS_QY",  "dispatch_seconds"),
        ("INCIDENT_TRAVEL_TM_SECONDS_QY", "travel_seconds"),
        ("INCIDENT_RESPONSE_SECONDS_QY",  "response_seconds"),
        ("FINAL_SEVERITY_LEVEL_CODE",     "final_severity"),
    ]:
        out[dst] = pd.to_numeric(
            out[src].str.replace(",", "", regex=False), errors="coerce"
        )
    out["incident_datetime"] = pd.to_datetime(
        out["INCIDENT_DATETIME"], format=DATE_FORMAT, errors="coerce"
    )
    return out

def fails_indicators(df):
    """True where either validity indicator is not 'Y'."""
    dispatch_ok = df["VALID_DISPATCH_RSPNS_TIME_INDC"].str.strip().str.upper() == "Y"
    incident_ok = df["VALID_INCIDENT_RSPNS_TIME_INDC"].str.strip().str.upper() == "Y"
    return ~(dispatch_ok & incident_ok)

def fails_missing_times(df):
    """True where any of the three durations is missing."""
    return (
        df["dispatch_seconds"].isna()
        | df["travel_seconds"].isna()
        | df["response_seconds"].isna()
    )

def fails_bad_date(df):
    """True where the incident date could not be parsed."""
    return df["incident_datetime"].isna()

def fails_bad_severity(df):
    """True where the final severity code is missing or not a number."""
    return df["final_severity"].isna()

def fails_duplicate_id(df):
    """True for the 2nd, 3rd... occurrence of an incident ID."""
    return df["INCIDENT_ID"].duplicated(keep="first")

def fails_zero_response(df):
    """True where response time is zero or negative."""
    return df["response_seconds"] <= 0

def fails_response_math(df):
    """True where dispatch + travel differs from response by more than 1 second."""
    diff = (df["response_seconds"] - (df["dispatch_seconds"] + df["travel_seconds"])).abs()
    return diff > 1

RULES = [
    ("invalid_date",           fails_bad_date),
    ("bad_severity",           fails_bad_severity),
    ("duplicate_incident_id",  fails_duplicate_id),
    ("invalid_indicator",      fails_indicators),
    ("missing_time",           fails_missing_times),
    ("zero_response",          fails_zero_response),
    ("response_math_mismatch", fails_response_math),
]

def split_good_and_rejects(df):
    """Return (good, rejects). Rejects get a 'reject_reason' column."""
    reason = pd.Series(pd.NA, index=df.index, dtype="object")
    for name, rule in RULES:
        newly_failed = rule(df) & reason.isna()   # only rows with no reason yet
        reason[newly_failed] = name
    rejects = df[reason.notna()].copy()
    rejects["reject_reason"] = reason[reason.notna()]
    good = df[reason.isna()].copy()
    return good, rejects
