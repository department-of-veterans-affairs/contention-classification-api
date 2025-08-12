# lh_brd_classification_ids

This data is used to decide if a condition code is expired.

## Research

These are for findings on what the data is used for and their findings.

### Usage Tracing

This is to document where the data is being used. Knowing where the data is used provides context for where we need to consider the Contention-Classification-API is affecting other services.

The POST endpoint "/hybrid-contention-classification" and "/ml-contention-classification" is where the data is utilized by production.
Tests do use the data, however, should not affect running processes.

For "lh_brd_classification_ids", trace was performed for commit [3b0120a](https://github.com/department-of-veterans-affairs/contention-classification-api/commit/3b0120abf3a1770226bf903996f394c33fb09106) on 18 July 2025.
