"""Unit tests for cleaning the dataset."""

import pandas as pd

from cleansing import (
    add_typed_columns,
    fails_bad_date,
    fails_bad_severity,
    fails_duplicate_id,
    fails_indicators,
    fails_missing_times,
    fails_response_math,
    fails_zero_response,
    split_good_and_rejects,
)

# Valid row. Every test starts from this and changes
# only the field it wants to break.
VALID_ROW = {
    "INCIDENT_ID": "1",
    "INCIDENT_DATETIME": "01/01/2005 04:52:16 AM",
    "FINAL_SEVERITY_LEVEL_CODE": "2",
    "VALID_DISPATCH_RSPNS_TIME_INDC": "Y",
    "VALID_INCIDENT_RSPNS_TIME_INDC": "Y",
    "DISPATCH_RESPONSE_SECONDS_QY": "59",
    "INCIDENT_TRAVEL_TM_SECONDS_QY": "440",
    "INCIDENT_RESPONSE_SECONDS_QY": "499",
}

def make_typed(*changes):
    """Build a typed table. Each item in `changes` is a dict of overrides
    for one row. make_typed({}) gives one valid row."""
    rows = [{**VALID_ROW, **change} for change in changes]
    return add_typed_columns(pd.DataFrame(rows))

def test_commas_are_removed_from_numbers():
    """A value like '1,219' becomes the number 1219."""
    df = make_typed({"INCIDENT_RESPONSE_SECONDS_QY": "1,219"})
    assert df.loc[0, "response_seconds"] == 1219

def test_valid_row_is_typed_correctly():
    """A valid row gets the right numbers and datetime."""
    df = make_typed({})
    assert df.loc[0, "dispatch_seconds"] == 59
    assert df.loc[0, "final_severity"] == 2
    assert df.loc[0, "incident_datetime"] == pd.Timestamp("2005-01-01 04:52:16")

def test_bad_number_becomes_nan_not_a_crash():
    """Text that is not a number becomes empty instead of stopping the job."""
    df = make_typed({"DISPATCH_RESPONSE_SECONDS_QY": "abc"})
    assert pd.isna(df.loc[0, "dispatch_seconds"])

def test_pm_time_is_read_on_a_12_hour_clock():
    """11:30 PM is read as 23:30."""
    df = make_typed({"INCIDENT_DATETIME": "03/15/2020 11:30:00 PM"})
    assert df.loc[0, "incident_datetime"] == pd.Timestamp("2020-03-15 23:30:00")

def test_valid_row_passes_every_rule():
    """A clean row is not flagged by any rule."""
    df = make_typed({})
    rules = [
        fails_indicators,
        fails_missing_times,
        fails_zero_response,
        fails_response_math,
        fails_duplicate_id,
        fails_bad_date,
        fails_bad_severity,
    ]
    for rule in rules:
        assert not rule(df).any(), rule.__name__

def test_indicator_n_fails():
    """An 'N' in a validity indicator fails the row."""
    df = make_typed({}, {"INCIDENT_ID": "2", "VALID_INCIDENT_RSPNS_TIME_INDC": "N"})
    assert fails_indicators(df).tolist() == [False, True]

def test_indicator_is_not_case_sensitive():
    """' y ' counts as 'Y'."""
    df = make_typed({"VALID_DISPATCH_RSPNS_TIME_INDC": " y "})
    assert not fails_indicators(df).iloc[0]

def test_missing_travel_time_fails():
    """An empty travel time fails the row."""
    df = make_typed({"INCIDENT_TRAVEL_TM_SECONDS_QY": None})
    assert fails_missing_times(df).iloc[0]

def test_zero_response_fails():
    """A response time of zero fails the row."""
    df = make_typed({
        "DISPATCH_RESPONSE_SECONDS_QY": "0",
        "INCIDENT_TRAVEL_TM_SECONDS_QY": "0",
        "INCIDENT_RESPONSE_SECONDS_QY": "0",
    })
    assert fails_zero_response(df).iloc[0]

def test_response_math_mismatch_fails():
    """Dispatch + travel must equal response."""
    df = make_typed({"INCIDENT_RESPONSE_SECONDS_QY": "600"})  # 59 + 440 != 600
    assert fails_response_math(df).iloc[0]

def test_response_math_allows_one_second_difference():
    """A difference of exactly one second is allowed."""
    df = make_typed({"INCIDENT_RESPONSE_SECONDS_QY": "500"})  # off by 1
    assert not fails_response_math(df).iloc[0]

def test_duplicate_flags_only_the_later_copy():
    """The first copy of an incident ID is kept, later copies fail."""
    df = make_typed({"INCIDENT_ID": "7"}, {"INCIDENT_ID": "7"})
    assert fails_duplicate_id(df).tolist() == [False, True]

def test_unparseable_date_fails():
    """A date that cannot be read fails the row."""
    df = make_typed({"INCIDENT_DATETIME": "not a date"})
    assert fails_bad_date(df).iloc[0]

def test_missing_severity_fails():
    """A missing severity code fails the row."""
    df = make_typed({"FINAL_SEVERITY_LEVEL_CODE": None})
    assert fails_bad_severity(df).iloc[0]

def test_split_counts_add_up_and_each_row_has_one_reason():
    """Good + rejected equals the input, and every reject has a reason."""
    df = make_typed(
        {"INCIDENT_ID": "1"},                                          # good
        {"INCIDENT_ID": "2", "VALID_INCIDENT_RSPNS_TIME_INDC": "N"},   # bad
        {"INCIDENT_ID": "3", "INCIDENT_DATETIME": "garbage"},          # bad
    )
    good, rejects = split_good_and_rejects(df)
    assert len(good) == 1
    assert len(rejects) == 2
    assert len(good) + len(rejects) == len(df)
    assert rejects["reject_reason"].notna().all()

def test_first_matching_rule_wins():
    """A row that fails two rules is recorded under the first one."""
    df = make_typed({
        "VALID_INCIDENT_RSPNS_TIME_INDC": "N",
        "INCIDENT_TRAVEL_TM_SECONDS_QY": None,
        "INCIDENT_RESPONSE_SECONDS_QY": None,
    })
    _, rejects = split_good_and_rejects(df)
    assert rejects["reject_reason"].tolist() == ["invalid_indicator"]

def test_good_rows_have_no_reject_reason_column():
    """Only rejected rows carry a reject_reason."""
    df = make_typed({})
    good, _ = split_good_and_rejects(df)
    assert "reject_reason" not in good.columns
