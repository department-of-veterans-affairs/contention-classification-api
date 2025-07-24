# Master Taxonomy

This data is used to match condition codes and names. 


## Research

These are for findings on what the data is used for and their findings. 

### Usage Tracing

This is to document where the data is being used. Knowing where the data is used provides context for where we need to consider the Contention-Classification-API is affecting other services. 

Trace start for "CC Taxonomy master"

1. `contention-classification-api/src/python_src/util/data/master_taxonomy/CC Taxonomy master - v0.2.csv`
1. `contention-classification-api/src/python_src/util/app_config.yaml`
   1. `contention-classification-api/src/python_src/util/app_config.yaml`
      ```yaml
      condition_dropdown_table:
         version_number: v0.2
         filename: "CC Taxonomy master"
      ```
      1. `contention-classification-api/src/python_src/util/app_utilities.py`
         ```python 
         contention_lut_csv_filename = (
            f"{app_config['condition_dropdown_table']['filename']} - {app_config['condition_dropdown_table']['version_number']}.csv"
         )

         contention_text_csv_filepath = os.path.join(
            os.path.dirname(__file__),
            "data",
            "master_taxonomy",
            contention_lut_csv_filename,
         )

         dropdown_expanded_table_inits = InitValues(
            csv_filepath=contention_text_csv_filepath,
            input_key=app_config["condition_dropdown_table"]["input_key"],
            classification_code=app_config["condition_dropdown_table"]["classification_code"],
            classification_name=app_config["condition_dropdown_table"]["classification_name"],
            active_selection=app_config["condition_dropdown_table"]["active_classification"],
            lut_default_value=default_lut_table,
         )
         dropdown_lookup_table = ContentionTextLookupTable(dropdown_expanded_table_inits)


         expanded_lookup_table = ExpandedLookupTable(
            init_values=dropdown_expanded_table_inits,
            common_words=app_config["common_words"],
            musculoskeletal_lut=app_config["musculoskeletal_lut"],
         )
         ```
         1. `contention-classification-api/src/python_src/util/data/simulations/classifiers.py`
            ```python 
            from python_src.util.app_utilities import expanded_lookup_table, ml_classifier
            # ...
            class ProductionClassifier(BaseClassifierForSimulation):
               name = "csv_lookup"

               def make_predictions(self, conditions: List[str]) -> bool:
                  predicted_classifications: List[str] = []
                  for condition in conditions:
                        try:
                           prediction = str(expanded_lookup_table.get(condition).get("classification_code"))
                        except Exception as e:
                           print("error: ", e)

                        predicted_classifications.append(prediction)
                  self.predictions = predicted_classifications
                  return len(self.predictions) == len(conditions)
            ```
            1. `contention-classification-api/src/python_src/util/data/simulations/run_simulations.py`
               ```python 
               from python_src.util.data.simulations.classifiers import (
                  BaseClassifierForSimulation,
                  MLClassifier,
                  ProductionClassifier,
               )
               # ...
               if __name__ == "__main__":
                  conditions_to_test, expected_classifications = _get_input_from_file()

                  classifiers: List[BaseClassifierForSimulation] = [ProductionClassifier(), MLClassifier()]

                  for c in classifiers:
                     print(f"---{c.name}---")

                     success = c.make_predictions(conditions_to_test)
                     if not success:
                           raise Exception("mismatch between length of conditions_to_test and predictions")
                     predictions_file = _write_predictions_to_file(conditions_to_test, expected_classifications, c)
                     labels = list(set(expected_classifications + c.predictions))
                     labels.sort()

                     metrics_file = _write_metrics_to_file(
                           classification_report(
                              expected_classifications, c.predictions, labels=labels, target_names=labels, zero_division=1
                           ),
                           c.name,
                     )

                     print(f"Outputs: {predictions_file}, {metrics_file}\n")

                  if len(classifiers) > 1:
                     _write_aggregate_predictions_to_file(
                           conditions_to_test, expected_classifications, classifiers, "aggregate_predictions"
                     )
               ```
            1. `contention-classification-api/tests/test_simulation_classifiers.py`
               ```python 
               from src.python_src.util.data.simulations.classifiers import MLClassifier, ProductionClassifier, RespiratoryClassifier
               # ...
               def test_production_classifier() -> None:
                  production_classifier = ProductionClassifier()
                  assert production_classifier.name == "csv_lookup"
                  production_classifier.make_predictions(["asthma", "acne", "gallstones"])
                  assert production_classifier.predictions == ["9012", "9016", "8968"]
                  production_classifier.make_predictions(["lorem", "ipsun", "dolor", "donut", "cookie"])
                  assert production_classifier.predictions == ["None"] * 5
               ```
               1. Issue: Unlikely 
                  1. Reason: Test should not affect running services.  
         2. `contention-classification-api/tests/test_data.py`
            ```python 
            def test_build_expanded_table() -> None:
            expanded = ExpandedLookupTable(
               init_values=dropdown_expanded_table_inits,
               common_words=app_config["common_words"],
               musculoskeletal_lut=app_config["musculoskeletal_lut"],
            )
            assert len(expanded.contention_text_lookup_table) == 1071
            ```
            1. Issue: Unlikely
               1. Reason: Test should not affect running services.  
         3. `contention-classification-api/tests/test_expanded_lookup.py`
            ```python 
            from src.python_src.util.expanded_lookup_table import ExpandedLookupTable
            ```
            1. `contention-classification-api/tests/test_expanded_lookup.py`
               ```python
               TEST_LUT = ExpandedLookupTable(
                  init_values=dropdown_expanded_table_inits,
                  common_words=app_config["common_words"],
                  musculoskeletal_lut=app_config["musculoskeletal_lut"],
               )
               ```
               1. Issue: Unlikely
                  1. Reason: Test should not affect running services.  
            2. `contention-classification-api/tests/test_expanded_lookup.py`
               ```python 
               @patch("src.python_src.util.expanded_lookup_table.ExpandedLookupTable._removal_pipeline")
               def test_prep_incoming_text_cause(mock_removal_pipeline: Mock) -> None:
                  test_str = "acl tear, due to something"
                  TEST_LUT.prep_incoming_text(test_str)
                  mock_removal_pipeline.assert_called_once_with("acl tear, ")
               ```
               1. Issue: Unlikely
                  1. Reason: Test should not affect running services.  
            3. `contention-classification-api/tests/test_expanded_lookup.py`
               ```python 
               @patch("src.python_src.util.expanded_lookup_table.ExpandedLookupTable._removal_pipeline")
               def test_prep_incoming_text_non_cause(mock_removal_pipeline: Mock) -> None:
                  test_str = "acl tear in my right knee"
                  TEST_LUT.prep_incoming_text(test_str)
                  mock_removal_pipeline.assert_called_once_with(test_str)
               ```
               1. Issue: Unlikely
                  1. Reason: Test should not affect running services.  
         4. `contention-classification-api/src/python_src/api.py`
            ```python 
            from .util.app_utilities import dc_lookup_table, dropdown_lookup_table, expanded_lookup_table
            # ...
            @app.get("/health")
            def get_health_status() -> Dict[str, str]:
               empty_tables = []
               if not len(dc_lookup_table):
                  empty_tables.append("DC Lookup")
               if not len(expanded_lookup_table):
                  empty_tables.append("Expanded Lookup")
            ```
            1. Issue: Unlikely
               1. `length` is not using `expanded_lookup_table` values 
         5. `contention-classification-api/src/python_src/util/classifier_utilities.py`
            ```python 
            from .expanded_lookup_table import ExpandedLookupTable
            # ...
            @log_contention_stats_decorator
            def classify_contention(contention: Contention, claim: VaGovClaim, request: Request) -> Tuple[ClassifiedContention, str]:
               lookup_table: Union[ExpandedLookupTable, ContentionTextLookupTable] = expanded_lookup_table

               classification_code, classification_name, classified_by = get_classification_code_name(contention, lookup_table)

               response = ClassifiedContention(
                  classification_code=classification_code,
                  classification_name=classification_name,
                  diagnostic_code=contention.diagnostic_code,
                  contention_type=contention.contention_type,
               )
               return response, classified_by
            ```
            1. `contention-classification-api/src/python_src/util/classifier_utilities.py`
               ```python
               def classify_claim(claim: VaGovClaim, request: Request) -> ClassifierResponse:
                  classified_contentions: list[ClassifiedContention] = []
                  for contention in claim.contentions:
                     classification = classify_contention(contention, claim, request)
                     classified_contentions.append(classification)

                  num_classified = len([c for c in classified_contentions if c.classification_code])

                  response = ClassifierResponse(
                     contentions=classified_contentions,
                     claim_id=claim.claim_id,
                     form526_submission_id=claim.form526_submission_id,
                     is_fully_classified=num_classified == len(classified_contentions),
                     num_processed_contentions=len(classified_contentions),
                     num_classified_contentions=num_classified,
                  )

                  return response
               ```
               1. `contention-classification-api/src/python_src/api.py`
                  ```python
                  from .util.classifier_utilities import classify_claim, ml_classify_claim, supplement_with_ml_classification
                  ```
                  1. `contention-classification-api/src/python_src/api.py`
                     ```python
                     @app.post("/expanded-contention-classification")
                     @log_claim_stats_decorator
                     def expanded_classifications(claim: VaGovClaim, request: Request) -> ClassifierResponse:
                        response = classify_claim(claim, request)
                        return response
                     ```
                     1. Issue: Likely 
                        1. Reason: API Endpoint
                  2. `contention-classification-api/src/python_src/api.py`
                     ```python
                     @app.post("/hybrid-contention-classification")
                     @log_claim_stats_decorator
                     def hybrid_classification(claim: VaGovClaim, request: Request) -> ClassifierResponse:
                        # classifies using expanded classification
                        response: ClassifierResponse = classify_claim(claim, request)

                        if response.is_fully_classified:
                           return response

                        response = supplement_with_ml_classification(response, claim)

                        num_classified = len([c for c in response.contentions if c.classification_code])
                        response.num_classified_contentions = num_classified
                        response.is_fully_classified = num_classified == len(response.contentions)

                        return response
                     ```
                     1. Issue: Likely 
                        1. API Endpoint
               2. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                  1. Issue: Unlikely
                     1. Reason: Test should not affect running services. 
         6. `contention-classification-api/src/python_src/util/logging_utilities.py`
            ```python 
            from .app_utilities import dropdown_lookup_table, dropdown_values, expanded_lookup_table
            # ... 
            def log_expanded_contention_text(
               logging_dict: Dict[str, Any], contention_text: str, log_contention_text: str
            ) -> Dict[str, Any]:
               """
               Updates the  logging dictionary with the contention text updates from the expanded classification method
               """
               processed_text = expanded_lookup_table.prep_incoming_text(contention_text)
               # only log these items if the expanded lookup returns a classification code
               if expanded_lookup_table.get(contention_text)["classification_code"]:
                  if log_contention_text == "unmapped contention text":
                        log_contention_text = f"unmapped contention text {[processed_text]}"
                  logging_dict.update(
                        {
                           "processed_contention_text": processed_text,
                           "contention_text": log_contention_text,
                        }
                  )
               # log none as the processed text if it is not in the LUT and leave unmapped contention text as is
               else:
                  logging_dict.update({"processed_contention_text": None})

               return logging_dict
            ```
            1. `contention-classification-api/src/python_src/util/logging_utilities.py` 
               ```python 
               def log_contention_stats(
                   ...
                  if request.url.path == "/expanded-contention-classification" or request.url.path == "/hybrid-contention-classification":
                     logging_dict = log_expanded_contention_text(logging_dict, contention.contention_text, log_contention_text)

                  log_as_json(logging_dict)
               ```
               1. Issue: Duplicate
         7. `contention-classification-api/tests/test_logging.py`
            ```python 
            from src.python_src.util.app_utilities import expanded_lookup_table
            ```
            1. Issue: Unlikely 
               1. Reason: Test should not affect running services. 
      2. `contention-classification-api/tests/test_lookup_table.py`
         ```python 
         term_columns = app_config["condition_dropdown_table"]["input_key"]
         classification_columns = [
            app_config["condition_dropdown_table"]["classification_code"],
            app_config["condition_dropdown_table"]["classification_name"],
            app_config["condition_dropdown_table"]["active_classification"],
         ]
         column_names = ",".join(term_columns + classification_columns)  # add string for mock csv strings
         ``` 
         1. `contention-classification-api/tests/test_lookup_table.py`
            ```python
            @pytest.fixture
            def mock_csv_strings() -> Dict[str, str]:
               return {
                  "diagnostic_csv": (
                        "DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n7710,6890,Tuberculosis\n6829,9012,Respiratory\n"
                  ),
                  "contention_csv": (
                        f"{column_names}\n"
                        "PTSD,,,,,,,,,,,,,,,,,,8989,Mental Disorders,Active\n"
                        "Knee pain,,,,,,,,,,,,,,,,,,8997,Knee,Active\n"
                  ),
            ```
         2. `contention-classification-api/tests/test_lookup_table.py`
            ```python
            def test_contention_text_lookup_table_duplicate_entries() -> None:
            """Test how ContentionTextLookupTable handles duplicate entries."""
            duplicate_csv = (
               f"{column_names}\n"
               "PTSD,,,,,,,,,,,,,,,,,,8989,Mental Disorders,Active\n"
               "PTSD,,,,,,,,,,,,,,,,,,9999,Different Mental Disorder,Active\n"
            )
            ```
   2. `contention-classification-api/src/python_src/util/app_config.yaml`
      ```yaml
      autosuggestion_table:
         version_number: v0.2
         filename: "CC Taxonomy master"
      ```
      1. `contention-classification-api/src/python_src/util/app_utilities.py`
         ```python
         autosuggestions_path = os.path.join(
            os.path.dirname(__file__),
            "data",
            "master_taxonomy",
            f"{app_config['autosuggestion_table']['filename']} - {app_config['autosuggestion_table']['version_number']}.csv",
         )

         dropdown_values = build_logging_table(
            autosuggestions_path,
            app_config["autosuggestion_table"]["autocomplete_terms"],
            app_config["autosuggestion_table"]["active_autocomplete"],
         )
         ```
         1. `contention-classification-api/src/python_src/util/logging_utilities.py`
            ```python 
            from .app_utilities import dropdown_lookup_table, dropdown_values, expanded_lookup_table
            ```
            1. `contention-classification-api/src/python_src/util/logging_utilities.py`
               ```python 
               is_in_dropdown = contention_text.strip().lower() in dropdown_values
               ```
               1. Issue: Duplicate 
      2. `contention-classification-api/tests/test_logging_dropdown_selections.py`
         ```python 
         def test_first_function(test_client: TestClient, mock_csv_data: str) -> None:
         """Test build_logging_table with mock data."""
         with patch("builtins.open", mock_open(read_data=mock_csv_data)):
            result = build_logging_table(
                  "mock_csv_filepath.csv",
                  app_config["autosuggestion_table"]["autocomplete_terms"],
                  app_config["autosuggestion_table"]["active_autocomplete"],
            )
         ```
         1. `contention-classification-api/tests/test_logging_dropdown_selections.py`
            ```python 
            dropdown_values = build_logging_table(
               autosuggestions_path,
               app_config["autosuggestion_table"]["autocomplete_terms"],
               app_config["autosuggestion_table"]["active_autocomplete"],
            )
            ```
            1. Issue: Unlikely
               1. Reason: Test should not affect running services. 
            2. `contention-classification-api/tests/test_logging_dropdown_selections.py`
            ```python
            dropdown_values = build_logging_table(
               autosuggestions_path,
               app_config["autosuggestion_table"]["autocomplete_terms"],
               app_config["autosuggestion_table"]["active_autocomplete"],
            )
            ```
            3. `contention-classification-api/src/python_src/util/logging_utilities.py`
               ```python 
               from .app_utilities import dropdown_lookup_table, dropdown_values, expanded_lookup_table
               # ...
               is_in_dropdown = contention_text.strip().lower() in dropdown_values
               # ...
               # Isn't this no longer the values being presented? 
               # ...
               logging_dict = {
                  "vagov_claim_id": sanitize_log(claim.claim_id),
                  "claim_type": sanitize_log(log_contention_type),
                  "classification_code": classification_code,
                  "classification_name": classification_name,
                  "contention_text": log_contention_text,
                  "diagnostic_code": sanitize_log(contention.diagnostic_code),
                  "is_in_dropdown": is_in_dropdown,
                  "is_lookup_table_match": classification_code is not None,
                  "is_multi_contention": is_multi_contention,
                  "endpoint": request.url.path,
                  "classification_method": classified_by,
               }

               if request.url.path == "/expanded-contention-classification" or request.url.path == "/hybrid-contention-classification":
                  logging_dict = log_expanded_contention_text(logging_dict, contention.contention_text, log_contention_text)

               log_as_json(logging_dict)
               ```
                  1. `contention-classification-api/src/python_src/util/logging_utilities.py`
                  ```python
                  def log_as_json(log: Dict[str, Any]) -> None:
                  """
                  Logs the dictionary as a JSON to enable easier parsing in DataDog
                  """
                  if "date" not in log.keys():
                     log.update({"date": datetime.now(tz=timezone.utc).isoformat()})
                  if "level" not in log.keys():
                     log.update({"level": "info"})
                  logging.info(json.dumps(log))
                  ```
               1. `contention-classification-api/src/python_src/util/app_utilities.py`
                  ```python 
                  autosuggestions_path = os.path.join(
                     os.path.dirname(__file__),
                     "data",
                     "master_taxonomy",
                     f"{app_config['autosuggestion_table']['filename']} - {app_config['autosuggestion_table']['version_number']}.csv",
                  )
                  ```
                  1. Issue: Duplicate
         2. Issue: Unlikely
            1. Reason: Test should not affect running services. 
      3. `contention-classification-api/tests/test_logging_lookup.py`
         ```python 
         filepath = os.path.join(
            "src",
            "python_src",
            "util",
            "data",
            "master_taxonomy",
            f"{app_config['autosuggestion_table']['filename']} - {app_config['autosuggestion_table']['version_number']}.csv",
         )
         ```
         1. Issue: Unlikely
            1. Reason: Test should not affect running services. 