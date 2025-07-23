# Master Taxonomy

This data is used to match condition codes and names. 

## Research

These are for findings on what the data is used for and their findings. 

### Usage Tracing

This is to document where the data is being used. Knowing where the data is used provides context for where we need to consider the Contention-Classification-API is affecting other services. 

Trace start for "CC Taxonomy master"

1. `contention-classification-api/src/python_src/util/data/master_taxonomy/CC Taxonomy master - v0.2.csv`
2. `contention-classification-api/src/python_src/util/app_config.yaml`
   1. `contention-classification-api/src/python_src/util/app_config.yaml`
      ```yaml
      condition_dropdown_table:
         version_number: v0.2
         filename: "CC Taxonomy master"
      ```
   2. `contention-classification-api/src/python_src/util/app_config.yaml`
      ```yaml
      autosuggestion_table:
         version_number: v0.2
         filename: "CC Taxonomy master"
      ```
      1. `contention-classification-api/tests/test_data.py`
         ```python
         app_config = load_config("src/python_src/util/app_config.yaml")
         ```
         1. Issue: Unlikely
            1. Reason: Test should not affect running services.
      2. `contention-classification-api/tests/test_expanded_lookup.py`
         ```python
         app_config = load_config("src/python_src/util/app_config.yaml")
         ```
         1. Issue: Unlikely
            1. Reason: Test should not affect running services. 
3. `vagov-claim-classification-data/taxonomy_autosuggestion/parse_autosuggestion.py`
   1. `vagov-claim-classification-data/taxonomy_autosuggestion/parse_autosuggestion.py`
      ```python
      READ_FILENAME: str = "taxonomy_autosuggestion/CC Taxonomy master - v0.1.csv"
      # ...
      if __name__ == "__main__":
         autosuggestion_terms = read_csv(READ_FILENAME)
         write_to_js(autosuggestion_terms, WRITE_FILENAME)
         print("done")
      # ...
      def write_to_js(data: list, filepath: str=None) -> None:
         """
         writes list of dicts to js file
         """
         c = 0
         js_obj: str = "export default {\n"
         for t in data:
            if "'" in t:
                  js_obj += f'  {c}: "{t}",\n'
            else:
                  js_obj += f"  {c}: '{t}',\n"
            c += 1
         js_obj += "}"

         with open(filepath, "w") as j:
            j.write(js_obj)
      ```
      1. Issue: Unlikely
         1. Reason: Printout to a file should not be an issue
