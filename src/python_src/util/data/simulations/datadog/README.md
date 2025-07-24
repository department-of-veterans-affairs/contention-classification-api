# Simulations: Inputs informed by Datadog

- [Process](#process)
- [Inputs, type A: contentention texts covered by the CSV lookup](#inputs-type-a-contentention-texts-covered-by-the-csv-lookup)
- [Inputs, type B: contentention texts NOT covered by the CSV lookup](#inputs-type-b-contentention-texts-not-covered-by-the-csv-lookup)

## Process
We can leverage application logging visible in Datadog Log Explorer to create sample inputs for simulations.

Among other data points, the logs show:
1) the text of the contention that the API was asked to classify
2) the name and code of the classification (or null values, if the csv lookup was unable to classify the contention)
3) the type of contention: whether it was submitted as a new condition, or as a claim for an increased disability rating ("claim for increase", CFI).


The Datadog Log Explorer allows for downloading results to a CSV file, which can then be further processed for compabitility with the simulator script.  Screenshot of the "Download as CSV" option:
<img src='https://github.com/user-attachments/assets/3b8f8ef9-1863-47ff-9adf-3544bba6096f' alt='screenshot of the "Download as CSV" option in Datadog' width=400/>


> For more about what data points are logged, see `def log_contention_stats()` and `def log_expanded_contention_text()` in [util/logging_utilities.py](https://github.com/department-of-veterans-affairs/contention-classification-api/blob/main/src/python_src/util/logging_utilities.py).


## Inputs, type A: contention texts covered by the CSV lookup

These are contention texts that have been successfully classified by the csv lookup.

The search parameters:

| tag | description |
| --- | --- |
| `index:main` | limit to the production environment  |
| `service:contention-classification-api` | limit to service `contention-classification-api`  |
| `-@contention_text:*unmapped*` |  exclude logs that have an attribute named `contention_text` that contains substring `unmapped` |
| `@classification_code:*` | limit to logs that have a value for attribute `classification_code`  |
| `@classification_name:*` |  limit to logs that have a value for attribute `classification_name`   |

[Link](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api%20%40classification_code%3A%2A%20%40classification_name%3A%2A&agg_m=count&agg_m_source=base&agg_t=count&clustering_pattern_field_path=%40contention_text&cols=%40contention_text%2C%40classification_code%2C%40classification_name&fromUser=true&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=desc&viz=stream&from_ts=1751728044281&to_ts=1751900844281&live=true) to this query in Datadog Log Explorer.

A sample of these results are in [2025-06-23.csv](./extracts/2025-06-23.csv) (5k rows)


## Inputs, type B: contention texts NOT covered by the CSV lookup

A sample of the contention texts not covered by the CSV lookup was collected through Datadog from June 30-July 7, 2025. This was collected by a modified logging payload (new attribute: `ml_sample`). It was realized that the implementation was susceptible to PII, thus this modified logging was discontinued, with collected data exported to Sharepoint and removed from Datadog.

The search parameters:

| tag | description |
| --- | --- |
| `index:main` |  limit to the production environment   |
| `service:contention-classification-api` | limit to service `contention-classification-api`  |
| `@ml_sample:*` |  limit to logs that have a value for attribute `ml_sample`    |
| -@classification_code:* | exclude logs that have an attribute named `classification_code` that has a value |

[Link](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api%20%40ml_sample%3A%2A%20-%40classification_code%3A%2A&agg_m=count&agg_m_source=base&agg_t=count&clustering_pattern_field_path=message&cols=%40ml_sample%2C%40classification_code%2C%40classification_method%2C%40classification_name%2C%40claim_type&index=main&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=time%2Cdesc&viz=stream&from_ts=1751894831291&to_ts=1751909231291&live=true) to this query in Datadog Log Explorer.
