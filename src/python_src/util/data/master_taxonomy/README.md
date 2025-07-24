# Master Taxonomy

This data is used to match condition codes and names. 

## Research

These are for findings on what the data is used for and their findings. 

### Usage Tracing

This is to document where the data is being used. Knowing where the data is used provides context for where we need to consider the Contention-Classification-API is affecting other services. 

The POST endpoint "/expanded-contention-classification" is where the data is utilized by production. 
Tests do use the data, however, should not affect running processes. 

For "CC Taxonomy master", trace was performed for commit [342de96](https://github.com/department-of-veterans-affairs/contention-classification-api/commit/342de964a0b63e48c3b6c5dfb523a7e3f676cc8f). 