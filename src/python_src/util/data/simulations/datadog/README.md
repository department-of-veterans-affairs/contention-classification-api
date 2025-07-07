# Simulations: Inputs informed by Datadog

From application logging visible in Datadog Log Explorer, we can see the contention classification requests sent to the Contention Classification API, and whether the API was able to determine classifications.

The Log Explorer allows for downloading results to a CSV file, which can then be processed for input to the simulator script. 

Screenshot of the "Download as CSV" option:  
<img src='https://github.com/user-attachments/assets/3b8f8ef9-1863-47ff-9adf-3544bba6096f' alt='screenshot of the "Download as CSV" option in Datadog' width=400/>

## Samples, type 1: covered by csv lookup

These are contention texts that have been successfully classified by the csv lookup.

These can be browsed in Datadog's Log Explorer with these search parameters:

| tag | description |
| --- | --- |
| `index:main` | limit to the production environment  |
| `service:contention-classification-api` | limit to service `contention-classification-api`  |
| `-@contention_text:*unmapped*` |  exclude logs that have an attribute named `contention_text` that contains substring `unmapped` |
| `@classification_code:*` | limit to logs that have a value for attribute `classification_code`  |
| `@classification_name:*` |  limit to logs that have a value for attribute `classification_name`   |

[Link](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api%20%40classification_code%3A%2A%20%40classification_name%3A%2A&agg_m=count&agg_m_source=base&agg_t=count&clustering_pattern_field_path=%40contention_text&cols=%40contention_text%2C%40classification_code%2C%40classification_name&fromUser=true&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=desc&viz=stream&from_ts=1751728044281&to_ts=1751900844281&live=true) to this query in Datadog Log Explorer.

A sample of these results are in [2025-06-23.csv](./extracts/2025-06-23.csv) (5k rows)


## Samples, type 2: not covered by csv lookup

In July 2025 we deployed a change to the logging to capture the contention texts that were NOT successfully classified by the csv lookup. These values are exposed in log attribute `ml_sample`.

These can be browsed in Datadog's Log Explorer with these search parameters:

| tag | description |
| --- | --- |
| `index:main` |  limit to the production environment   |
| `service:contention-classification-api` | limit to service `contention-classification-api`  |
| `@ml_sample:*` |  limit to logs that have a value for attribute `ml_sample`    |

[Link](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api%20%40ml_sample%3A%2A&agg_m=count&agg_m_source=base&agg_t=count&cols=%40ml_sample%2C%40classification_code%2C%40classification_method%2C%40classification_name%2C%40claim_type&fromUser=true&index=main&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=time%2Cdesc&viz=stream&from_ts=1751727109483&to_ts=1751899909483&live=true) to this query in Datadog Log Explorer.
