# lh_brd_classification_ids

## Research

### Usage Tracing

Trace starts for "lh_brd_classification_ids"

1. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
   1. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
      ```python
      CLASSIFICATION_NAMES_BY_CODE = get_classification_names_by_code()
      ```
      1. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
         ```python
         def get_classification_name(classification_code: int) -> Optional[str]:
            return CLASSIFICATION_NAMES_BY_CODE.get(classification_code)
         ```
         1. `contention-classification-api/tests/test_brd_classification_codes.py`
            1. Issue: Unlikely
               1. Reason: Test
      2. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
         ```python
         CLASSIFICATION_CODES_BY_NAME = {v: k for k, v in CLASSIFICATION_NAMES_BY_CODE.items()}
         # ...
         def get_classification_code(classification_name: str) -> Optional[int]:
            return CLASSIFICATION_CODES_BY_NAME.get(classification_name)
         ```
         1. `contention-classification-api/tests/test_brd_classification_codes.py`
            1. Issue: Unlikely
               1. Reason: Test
         2. `contention-classification-api/tests/test_classifier_utilities.py`
            1. Issue: Unlikely
               1. Reason: Test
         3. `contention-classification-api/src/python_src/util/classifier_utilities.py`
            ```python
            classification_code=get_classification_code(classifications[i]),
            classified_contention = ClassifiedContention(...)
            classified_contentions.append(classified_contention)
            return AiResponse(classified_contentions=classified_contentions,)
            def ml_classify_claim(contentions: AiRequest) -> AiResponse:
            ```
            1. `contention-classification-api/src/python_src/util/classifier_utilities.py`
               ```python
               ai_response = ml_classify_claim(ai_request)
               response = update_classifications(response, non_classified_indices, ai_response)
               return response
               # this function
               def supplement_with_ml_classification(response: ClassifierResponse, claim: VaGovClaim) -> ClassifierResponse:
               ```
               1. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                  1. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                     ```python
                     @patch("src.python_src.api.supplement_with_ml_classification")
                     def test_hybrid_classifier_fully_classified(
                     ```
                     1. Issue: Unlikely
                        1. Reason: Test
                  2. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                     ```python
                     @patch("src.python_src.api.supplement_with_ml_classification")
                     def test_hybrid_classifier_partially_classified(
                     ```
                     1. Issue: Unlikely
                        1. Reason: Test
               2. `contention-classification-api/src/python_src/util/classifier_utilities.py`
                  ```python
                  response = supplement_with_ml_classification(response, claim)
                  # sent out
                  return response
                  # this is the function
                  @app.post("/hybrid-contention-classification")
                  @log_claim_stats_decorator
                  def hybrid_classification(claim: VaGovClaim, request: Request) -> ClassifierResponse:
                  ```
                  1. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                     ```python
                     test_client.post("/hybrid-contention-classification", json=test_claim.model_dump())
                     ```
                     1. Issue: Unlikely
                        1. Reason: Test
                  1. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                     ```python
                     test_response = test_client.post("/hybrid-contention-classification", json=test_claim.model_dump())
                     ```
                     1. Issue: Unlikely
                        1. Reason: Test
                  1. `contention-classification-api/tests/test_logging.py`
                     ```python
                     hybrid_request = Request(scope={"type": "http","method": "POST","path": "/hybrid-contention-classification","headers": Headers(),})
                     ```
                     1. `contention-classification-api/tests/test_logging.py`
                        ```python
                        log_contention_stats(test_contention,classified_contention,test_claim,hybrid_request,classified_by,)
                        ```
                        1. `contention-classification-api/src/python_src/util/logging_utilities.py`
                           ```python
                           def log_contention_stats(contention: Contention,classified_contention: ClassifiedContention,claim: VaGovClaim,request: Request,classified_by: str,)
                           ```
                           1. Follow: `request: Request` / `hybrid_request`
                           1. `contention-classification-api/src/python_src/util/logging_utilities.py`
                              ```python
                              "endpoint": request.url.path,
                              ```
                              1. `contention-classification-api/src/python_src/util/logging_utilities.py`
                                 ```python
                                 if request.url.path == "/expanded-contention-classification" or request.url.path == "/hybrid-contention-classification":
                                    logging_dict = log_expanded_contention_text(logging_dict, contention.contention_text, log_contention_text)
                                 ```
                                 1. Issue: Unlikely
                                    1. Reason: URL.Path is not the contention codes from lh_brd_classification_ids
               3. `contention-classification-api/src/python_src/api.py`
                  ```python
                  response = supplement_with_ml_classification(response, claim)
                  # sent out
                  return response
                  # api endpoint
                  @app.post("/hybrid-contention-classification")
                  @log_claim_stats_decorator
                  def hybrid_classification(claim: VaGovClaim, request: Request) -> ClassifierResponse:
                  ```
                  1. Issue: Maybe
                     1. Reason: API Endpoint
                  2. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                     ```python
                     test_client.post("/hybrid-contention-classification", json=test_claim.model_dump())
                     ```
                     1. Issue: Unlikely
                        1. Reason: Test
                  3. `contention-classification-api/tests/test_logging.py`
                     ```python
                     hybrid_request = Request(scope={"type": "http","method": "POST","path": "/hybrid-contention-classification","headers": Headers(),})
                     ```
                     1. Issue: Duplicate
            1. `contention-classification-api/src/python_src/api.py`
               ```python
               @app.post("/ml-contention-classification")
               def ml_classifications_endpoint(contentions: AiRequest) -> AiResponse:
                  response = ml_classify_claim(contentions)
                  return response
               ```
               1. Issue: Maybe
                  1. Reason: API Endpoint
               2. `contention-classification-api/src/python_src/util/app_config.yaml`
                  ```yaml
                  ai_classification_endpoint:
                     url: 'http://localhost:8120/'
                     endpoint: 'ml-contention-classification'
                  ```
                  1. Don't see `ai_classification_endpoint` being explicitly referenced
                  2. Issue: Unlikely
                     1. Reason: `app_config.yaml` is used a lot, but don't see the key-value being referenced
            2. `contention-classification-api/tests/test_classifier_utilities.py`
               ```python
               ai_response = ml_classify_claim(TEST_AI_REQUEST)
               ```
               1. Issue: Unlikely
                  1. Reason Test
2. `vagov-contention-cleaning/core/data/filepaths.py`
   ```python
   LH_BRD_JSON = os.path.join(CLASSIFICATION_DIR, "lh_brd_classification_ids.json")
   ```
   1. `vagov-contention-cleaning/core/data/classification_codes.py`
      ```python
      new_path = os.path.join(ROOT_DIR, Filepaths.LH_BRD_JSON.value)
      ```
      1. This is duplicate
3. `vagov-claim-classification-data/notebooks/1-data/10-caj-eda_20221222`
   ```xml
   " <FilePaths.LH_BRD_JSON: 'resources/classification_ids/lh_brd_classification_ids.json'>,\n",
   ```
   1. Issue: Unlikely
      1. Reason: Self-reference
4. `abd-vro/domain-cc/cc-app/src/python_src/util/brd_classification_codes.py`
   ```python
   BRD_CLASSIFICATIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "lh_brd_classification_ids.json")

   def get_classification_names_by_code():
    name_by_code = {}
    with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
        disability_items = json.load(fh)["items"]
        for item in disability_items:
            name_by_code[item["id"]] = item["name"]
    return name_by_code

    CLASSIFICATION_NAMES_BY_CODE = get_classification_names_by_code()

   def get_classification_name(classification_code):
      return CLASSIFICATION_NAMES_BY_CODE.get(classification_code)
   ```
   1. Issue: Unlikely
      1. Reason: No usage found
5. `abd-vro-internal/domain-cc/cc-app/src/python_src/util/brd_classification_codes.py`
   ```python
   BRD_CLASSIFICATIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "lh_brd_classification_ids.json")

   def get_classification_names_by_code():
      name_by_code = {}
      with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
         disability_items = json.load(fh)["items"]
         for item in disability_items:
               name_by_code[item["id"]] = item["name"]
      return name_by_code

   CLASSIFICATION_NAMES_BY_CODE = get_classification_names_by_code()

   def get_classification_name(classification_code):
      return CLASSIFICATION_NAMES_BY_CODE.get(classification_code)
   ```
   1. Issue: Unlikely
      1. Reason: No usage found
6. `abd-vro/domain-cc/cc-app/src/python_src/util/brd_classification_codes.py`
   ```python
   BRD_CLASSIFICATIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "lh_brd_classification_ids.json")

   def get_classification_names_by_code() -> Dict[int, str]:
    name_by_code = {}
    with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
        disability_items = json.load(fh)["items"]
        for item in disability_items:
            name_by_code[item["id"]] = item["name"]
    return name_by_code
   ```
   1. `contention-classification-api/tests/test_brd_classification_codes.py`
      1. Issue: Unlikely
         1. Reason: Test
   2. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
      ```python
      CLASSIFICATION_NAMES_BY_CODE = get_classification_names_by_code()
      CLASSIFICATION_CODES_BY_NAME = {v: k for k, v in CLASSIFICATION_NAMES_BY_CODE.items()}
      ```
      1. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
         ```python
         def get_classification_name(classification_code: int) -> Optional[str]:
            return CLASSIFICATION_NAMES_BY_CODE.get(classification_code)
         ```
         1. `contention-classification-api/tests/test_brd_classification_codes.py`
            1. Issue: Unlikely
               1. Test
      2. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
         ```python
         def get_classification_code(classification_name: str) -> Optional[int]:
            return CLASSIFICATION_CODES_BY_NAME.get(classification_name)
         ```
         1. `contention-classification-api/tests/test_brd_classification_codes.py`
            1. Issue: Unlikely
               1. Reason: Test
         2. `contention-classification-api/src/python_src/util/classifier_utilities.py`
            ```python
            classified_contention = ClassifiedContention(
               classification_code=get_classification_code(classifications[i]),
                    classified_contentions.append(classified_contention)
            return AiResponse(
               classified_contentions=classified_contentions,
            )
            # this function
            def ml_classify_claim(contentions: AiRequest) -> AiResponse:
            ```
            1. Issue: N/A
               1. Reason: Duplicate
         3. `contention-classification-api/tests/test_classifier_utilities.py`
            1. Issue: Unlikely
               1. Reason: Test
7. `vagov-claim-classification-data/resources/classification_codes/lh_brd_classification_ids.json`
   1. Issue: Unlikely
      1. Reason: No usage found
8. `vagov-contention-cleaning/resources/classification_codes/lh_brd_classification_ids.json`
   1. Issue: Unlikely
      1. Reason: No usage found
9. `vagov-claim-classification-data/core/data/filepaths.py`
   ```python
   LH_BRD_JSON = os.path.join(CLASSIFICATION_DIR, "lh_brd_classification_ids.json")
   ```
   1. `vagov-claim-classification-data/core/data/classification_codes.py`
      ```python
      new_path = os.path.join(ROOT_DIR, Filepaths.LH_BRD_JSON.value)
      new_map = read_lh_classification_json(new_path)
      return old_map, new_map
      # this function
      def get_classification_code_maps():
      ```
      1. `vagov-claim-classification-data/core/data/classification_codes.py`
         ```python
         old_ids, new_ids = get_classification_code_maps()
         df['in_old_list'] = np.where(df['CNTNTN_CLSFCN_ID'].isin(old_ids), True, False)
         df['in_new_list'] = np.where(df['CNTNTN_CLSFCN_ID'].isin(new_ids), True, False)
         df['old_or_new'] = df['in_old_list'] | df['in_new_list']
         return df
         # this function
         def add_classification_list_indicator_cols_to_df(df):
         ```
         1. Issue: Unlikely
            1. Reason: No usage found
      2. `vagov-claim-classification-data/create_simple_contention_mapping.py`
         ```python
         _, new_class_dict = get_classification_code_maps()
         ```
         1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
            ```python
            labels = list(new_class_dict.keys())
            totals_confusion_matrix = create_confusion_matrix(evaluation_data, labels, 'sum')
            total_sum_metrics, _ = get_metrics_dict(evaluation_data, totals_confusion_matrix, labels, 'sum')
            metrics_df = pd.DataFrame.from_dict(data=total_sum_metrics, orient='index', columns=['class_id', 'class_name', 'precision', 'recall', 'f1-score', 'support'])
            metrics_df['class_id'] = metrics_df.index
            metrics_df['class_name'] = metrics_df.apply(lambda x: new_class_dict[x.class_id], axis=1)
            metrics_df.reset_index(level=0, drop=True, inplace=True)
            metrics_df.to_csv(class_perf_path_str, index=False)
            ```
               1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                  ```python
                  class_perf_path_str = str(version_subdir_path.joinpath(Filepaths.LUT_CLASS_PERF_FNAME.value))
                  ```
               2. `vagov-claim-classification-data/core/data/filepaths.py`
                  ```python
                  LUT_CLASS_PERF_FNAME = "class_perf_data.csv"
                  ```
                  1. Issue: Unlikely
                     1. Reason: No usage found
         2. `vagov-claim-classification-data/create_simple_contention_mapping.py`
            ```python
            class_counts = create_class_counts(
               training_data, 'CLMANT_TXT_CLEAN', 'CNTNTN_CLSFCN_ID', new_class_dict, totals_column)
            confidence_scores = compute_confidence_scores(class_counts)
            ```
            1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
               ```python
               lut = create_lookup_table(confidence_scores, CONF_SCORE_THRESHOLD)
               totals_confusion_matrix = create_confusion_matrix(evaluation_data, labels, 'sum')
               ```
               1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                  ```python
                  lookup_scorer = ContentionMap(lut)
                  evaluation_data['predicted_class_id'] = lookup_scorer.predict(evaluation_data['CLMANT_TXT_CLEAN'])
                  ```
                  1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                     ```python
                     totals_confusion_matrix = create_confusion_matrix(evaluation_data, labels, 'sum')
                     total_sum_metrics, _ = get_metrics_dict(evaluation_data, totals_confusion_matrix, labels, 'sum')
                     metrics_df = pd.DataFrame.from_dict(data=total_sum_metrics, orient='index', columns=['class_id', 'class_name', 'precision', 'recall', 'f1-score', 'support'])
                     metrics_df['class_id'] = metrics_df.index
                     metrics_df['class_name'] = metrics_df.apply(lambda x: new_class_dict[x.class_id], axis=1)
                     metrics_df.reset_index(level=0, drop=True, inplace=True)
                     metrics_df.to_csv(class_perf_path_str, index=False)
                     ```
                     1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                        ```python
                        class_perf_path_str = str(version_subdir_path.joinpath(Filepaths.LUT_CLASS_PERF_FNAME.value))
                        ```
                        1. `vagov-claim-classification-data/core/data/filepaths.py`
                           ```python
                           LUT_CLASS_PERF_FNAME = "class_perf_data.csv"
                           ```
                           1. Issue: Unlikely
                              1. Reason: No usage found
               2. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                  ```python
                  write_dict_to_json(lut_json_path_str, lut)
                  ```
                  1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                     ```python
                     lut_json_path_str = str(version_subdir_path.joinpath(Filepaths.LUT_FNAME.value))
                     ```
                     1. `vagov-claim-classification-data/core/data/filepaths.py`
                        ```python
                        LUT_FNAME = "lookup_table.json"
                        ```
                        1. Issue: Unlikely
                           1. No usage found
            2. `vagov-claim-classification-data/create_simple_contention_mapping.py`
               ```python
               dSweep_conf_score = create_plot_of_model_performance(evaluation_data, 'CLMANT_TXT_CLEAN', 'CNTNTN_CLSFCN_ID', confidence_scores)
               dSweep_conf_score.plot.area(y=['CORRECT_LABEL', 'INCORRECT_LABEL', 'NO_LABEL'])
               dSweep_conf_score.sort_values('THRESHOLD', ascending=False, inplace=True)
               dSweep_conf_score.to_csv(acc_data_path_str, index=True)
               ```
               1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                  ```python
                  acc_data_path_str = str(version_subdir_path.joinpath(Filepaths.LUT_PERF_TABLE_FNAME.value))
                  ```
                  1. `vagov-claim-classification-data/core/data/filepaths.py`
                     ```python
                     LUT_PERF_TABLE_FNAME = "accuracy_data.csv"
                     ```
                     1. Issue: Unlikely
                        1. Reason: No usage found
            3. `vagov-claim-classification-data/create_simple_contention_mapping.py`
               ```python
               confidence_scores.to_csv(conf_score_path_str, index=False)
               ```
               1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                  ```python
                  conf_score_path_str = str(version_subdir_path.joinpath(Filepaths.LUT_CONFIDENCE_SCORES_FNAME.value))
                  ```
                  1. `vagov-claim-classification-data/core/data/filepaths.py`
                     ```python
                     LUT_CONFIDENCE_SCORES_FNAME = "confidence_scores.csv"
                     ```
                     1. Issue: Unlikely
                        1. No usage found
         3. `vagov-claim-classification-data/create_simple_contention_mapping.py`
            ```python
            metrics_df['class_name'] = metrics_df.apply(lambda x: new_class_dict[x.class_id], axis=1)
            ```
            1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
               ```python
               metrics_df.to_csv(class_perf_path_str, index=False)
               ```
               1. `vagov-claim-classification-data/create_simple_contention_mapping.py`
                  ```python
                  class_perf_path_str = str(version_subdir_path.joinpath(Filepaths.LUT_CLASS_PERF_FNAME.value))
                  ```
                  1. `vagov-claim-classification-data/core/data/filepaths.py`
                     ```python
                     LUT_CLASS_PERF_FNAME = "class_perf_data.csv"
                     ```
                     1. Issue: Unlikely
                        1. Reason: No usage found
   2. `vagov-claim-classification-data/core/data/classification_codes.py`
      ```python
      new_path = os.path.join(ROOT_DIR, Filepaths.LH_BRD_JSON.value)
      items = read_json_to_dict(new_path)['items']
      data = [[item_dict['id'], item_dict['name'], item_dict['endDateTime']]
         for item_dict in items]
      return pd.DataFrame(data, columns=columns)
      # this function
      def get_lh_brd_classification_codes_as_df():
      ```
      1. Issue: Unlikely
         1. Reason: No usage found
