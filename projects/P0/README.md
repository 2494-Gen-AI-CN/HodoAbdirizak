# Project 0: Data Warehouse and Analytics for a Client

Partner repo: [Thanujann Dayaparan](https://github.com/2494-Gen-AI-CN/ThanujannDayaparan)<br>
Slide Deck: [Canva](https://canva.link/4bbbo1h6vmz58wj)

### Business Case
**Client:** The Committee on Fire and Emergency Management, New York City Council

**Inquiry:** The committee has been given a one-off budget to fund new ambulance tours, meaning staffed ambulance shifts. The chair has to decide where and when they go before the budget hearing.

Press coverage and the Independent Budget Office have reported that response times for the most serious calls have gotten worse over the past decade. The chair wants to know what the data says before choosing.

**Business Questions:**
<ol>
  <li>How have response times for the most serious calls changed year by year?</li>
  <li>Which boroughs and dispatch areas are slowest for the most serious calls?</li>
  <li>Is the delay in dispatching (call to ambulance assigned) or in travel (assigned to on scene)?</li>
  <li>When are responses slowest, by hour of day and day of week?</li>
  <li>Did areas that received extra ambulance capacity improve afterwards?</li>
</ol>

## Environment Variables
- Create a Google Cloud account, and verify you are logged in through the console.
- Create a Google Cloud project and get it's ID.
- Place your project ID in your copy of the .env file.

## Config-driven ingestion

The ingestion job reads [config.yaml](./config.yaml) for the BigQuery project,
raw and warehouse datasets, and each raw source's file path and format. Run it
from the project directory with:

```
python ingest/upload_data.py
```

To add a raw source, add an entry under `sources` with a unique BigQuery table
name, a file path relative to the project directory, and `format: csv` or
`format: json`. JSON sources must be newline-delimited JSON. The job loads each
source into the configured raw dataset. The EMS cleansing transform is
opt-in; configure `transform: ems_incidents`, `clean_table`, and `reject_table`
for a source that uses the EMS schema.

## Data cleansing

The ingestion job validates every record with pandas before it reaches BigQuery.
A record that fails goes to the `rejects_ems_incident` table with **one reason**
and the job carries on with the rest.

### Rules

The client needs trustworthy response times. A wrong or impossible time would
distort the answers, so the rules remove records whose timings cannot be relied on. A row that fails several rules is recorded once, under the **first** rule it fails. 

| # | Reject reason | Rejection criteria | Why |
|---|---|---|---|
| 1 | `invalid_date` | `INCIDENT_DATETIME` cannot be read as `MM/DD/YYYY hh:mm:ss AM/PM` | Without a date the call cannot be placed in time |
| 2 | `bad_severity` | `FINAL_SEVERITY_LEVEL_CODE` is missing or not a number | Severity defines the "most serious" calls (code < 3) |
| 3 | `duplicate_incident_id` | the `INCIDENT_ID` has already appeared | One row per incident |
| 4 | `invalid_indicator` | `VALID_DISPATCH_RSPNS_TIME_INDC` or `VALID_INCIDENT_RSPNS_TIME_INDC` is not `Y` | The data owner marks these timings as unreliable |
| 5 | `missing_time` | dispatch, travel or response seconds is empty | The fact table needs all three measures |
| 6 | `zero_response` | response seconds is 0 or negative | An ambulance cannot arrive at the instant of the call |
| 7 | `response_math_mismatch` | dispatch + travel differs from response by more than 1 second | Response is defined as dispatch plus travel, so a mismatch signals an error |
| 8 | `implausible_duration` | dispatch or response exceeds **4 hours** (14,400 s) | Extreme outliers would distort the results |

### Formatting fixes applied (not rejections)

- Numbers with thousands separators (for example `1,219`) have the comma removed.
- Dates are parsed with an explicit format, so `01/05/2005` is never ambiguous.
- Text indicators are trimmed and upper-cased before comparing, so ` y ` counts as `Y`.

### Results

First 1,000 rows (sample): 942 loaded, 58 rejected.

| Reject reason | Rows |
|---|---|
| invalid_indicator | 54 |
| zero_response | 3 |
| implausible_duration | 1 |


## Tests

The cleansing and transform functions in `ingest/cleansing.py` have unit tests
in `tests/test_cleansing.py`, written with pytest.

### Run the tests

```
pip install -r requirements.txt
pytest -v
```