# Simulations: Inputs informed by Datadog


From application logging visible in Datadog, we can see which contention texts have been successfully classified by the production classifier (ie the CSV lookup).


A subset of results from a sample [query](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api&agg_m=count&agg_m_source=base&agg_t=count&clustering_pattern_field_path=%40contention_text&cols=host%2Cservice&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=desc&viz=pattern&from_ts=1748107121936&to_ts=1750699121936&live=true)  are in [extract-2025-06-23T18_22_26.csv](./extract-2025-06-23T18_22_26.csv) (5k rows)