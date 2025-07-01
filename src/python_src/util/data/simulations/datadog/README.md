# Simulations: Inputs informed by Datadog


From application logging visible in Datadog, we can see which contention texts have been successfully classified by the production classifier (ie the CSV lookup).


A subset of results from a sample, rough [query](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api%20-%40contention_text%3A%2Aunmapped%2A%20%40classification_code%3A%2A%20%40claim_type%3Anew&agg_m=count&agg_m_source=base&agg_t=count&clustering_pattern_field_path=%40contention_text&cols=host%2Cservice&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=desc&viz=pattern&from_ts=1748112766095&to_ts=1750704766095&live=true) - it needs refinement - are in [2025-06-23.csv](./extracts/2025-06-23.csv) (5k rows)
