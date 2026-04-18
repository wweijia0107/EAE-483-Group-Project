# Data Dictionary

This repository standardizes AQS and OpenAQ PM2.5 records into a shared audit schema.

| Field | Meaning |
| --- | --- |
| `provider` | Data source name, either `AQS` or `OpenAQ`. |
| `station_id` | Source-specific monitor or sensor identifier. |
| `pair_id` | Shared pairing key used for the reproducible sample calibration workflow. |
| `pollutant` | Pollutant name. This project uses `PM2.5`. |
| `timestamp_utc` | UTC timestamp for the observation. |
| `timestamp_local` | Local timestamp for the observation. |
| `date` | Daily normalized local date used in summaries and matching. |
| `latitude` | Monitor latitude in WGS84. |
| `longitude` | Monitor longitude in WGS84. |
| `units` | Observation units, expected to be `ug/m3` in the sample workflow. |
| `value` | PM2.5 concentration value. |
| `qa_flag` | Simple QA or maintenance flag supplied by the source. |
| `expected_count` | Expected contributing sub-daily readings for the day. |
| `observed_count` | Observed contributing sub-daily readings for the day. |
| `percent_complete` | Coverage completion percentage for the day. |

