# Simulations: Inputs informed by Datadog


From application logging visible in Datadog, we can see the contention texts on which the csv lookup was applied and whether the csv lookup was able to determine a classification.


## Samples, type 1: covered by csv lookup

These are contention texts that have been successfully classified by the csv lookup.

These can be browsed the Datadog log explorer with these search parameters:

| tag | description |
| --- | --- |
| `index:main` | limit to the production environment  |
| `service:contention-classification-api` | limit to service `contention-classification-api`  |
| `-@contention_text:*unmapped*` |  exclude logs that have an attribute named `contention_text` that contains substring `unmapped` |
| `@classification_code:*` | limit to logs that have a value for attribute `classification_code`  |
| `@classification_name:*` |  limit to logs that have a value for attribute `classification_name`   |


Datadog [link](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api%20%40classification_code%3A%2A%20%40classification_name%3A%2A&agg_m=count&agg_m_source=base&agg_t=count&clustering_pattern_field_path=%40contention_text&cols=%40contention_text%2C%40classification_code%2C%40classification_name&fromUser=true&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=desc&viz=stream&from_ts=1751728044281&to_ts=1751900844281&live=true) to this query in Log Explorer.

A sample of these results are in [2025-06-23.csv](./extracts/2025-06-23.csv) (5k rows)


## Samples, type 2: not covered by csv lookup

In July 2025 we deployed a change to the logging to capture the contention texts that were NOT successfully classified by the csv lookup. These values are exposed in log attribute `ml_sample`.

These can be browsed the Datadog log explorer with these search parameters:
`index:main` `service:contention-classification-api` `@ml_sample:*`

| tag | description |
| --- | --- |
| `index:main` |  limit to the production environment   |
| `service:contention-classification-api` | limit to service `contention-classification-api`  |
| `@ml_sample:*` |  limit to logs that have a value for attribute `ml_sample`    |

Datadog [link](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api%20%40ml_sample%3A%2A&agg_m=count&agg_m_source=base&agg_t=count&cols=%40ml_sample%2C%40classification_code%2C%40classification_method%2C%40classification_name%2C%40claim_type&fromUser=true&index=main&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=time%2Cdesc&viz=stream&from_ts=1751727109483&to_ts=1751899909483&live=true) to this query in Log Explorer.
