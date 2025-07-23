# lh_brd_classification_ids

This data is used to decide if a condition code is expired. 

## Research

These are for findings on what the data is used for and their findings. 

### Usage Tracing

This is to document where the data is being used. Knowing where the data is used provides context for where we need to consider the Contention-Classification-API is affecting other services. 

Trace starts for "lh_brd_classification_ids"

1. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
   ```python 
   # sourced from Lighthouse Benefits Reference Data /disabilities endpoint:
   # https://developer.va.gov/explore/benefits/docs/benefits_reference_data?version=current
   BRD_CLASSIFICATIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "lh_brd_classification_ids.json")


   def get_classification_names_by_code() -> Dict[int, str]:
      with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
         brd_classification_list = json.load(fh)["items"]
      brd_classification_dict = {}
      for item in brd_classification_list:
         if item.get("endDateTime"):
               try:
                  item_datetime = datetime.datetime.strptime(item.get("endDateTime"), "%Y-%m-%dT%H:%M:%SZ")
                  if item_datetime is None or item_datetime < datetime.datetime.now():
                     continue
               except Exception as e:
                  logging.error(f"endDateTime format error: {e}")
                  continue
         brd_classification_dict[item["id"]] = item["name"]
      return brd_classification_dict
   ```
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
               1. Reason: Test should not affect running services. 
      2. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
         ```python
         CLASSIFICATION_CODES_BY_NAME = {v: k for k, v in CLASSIFICATION_NAMES_BY_CODE.items()}
         # ...
         def get_classification_code(classification_name: str) -> Optional[int]:
            return CLASSIFICATION_CODES_BY_NAME.get(classification_name)
         ```
         1. `contention-classification-api/tests/test_brd_classification_codes.py`
            1. Issue: Unlikely
               1. Reason: Test should not affect running services. 
         2. `contention-classification-api/tests/test_classifier_utilities.py`
            1. Issue: Unlikely
               1. Reason: Test should not affect running services. 
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
                        1. Reason: Test should not affect running services. 
                  2. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                     ```python
                     @patch("src.python_src.api.supplement_with_ml_classification")
                     def test_hybrid_classifier_partially_classified(
                     ```
                     1. Issue: Unlikely
                        1. Reason: Test should not affect running services. 
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
                        1. Reason: Test should not affect running services. 
                  1. `contention-classification-api/tests/test_ml_classification_endpoint.py`
                     ```python
                     test_response = test_client.post("/hybrid-contention-classification", json=test_claim.model_dump())
                     ```
                     1. Issue: Unlikely
                        1. Reason: Test should not affect running services. 
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
                        1. Reason: Test should not affect running services. 
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
                  1. Reason: Test should not affect running services. 
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
      1. Reason: This references the original starting file 
4. `contention-classifiction-api/src/python_src/util/brd_classification_codes.py`
   ```python
   BRD_CLASSIFICATIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "lh_brd_classification_ids.json")

   def get_classification_names_by_code() -> Dict[int, str]:
      with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
         brd_classification_list = json.load(fh)["items"]
      brd_classification_dict = {}
      for item in brd_classification_list:
         if item.get("endDateTime"):
               try:
                  item_datetime = datetime.datetime.strptime(item.get("endDateTime"), "%Y-%m-%dT%H:%M:%SZ")
                  if item_datetime is None or item_datetime < datetime.datetime.now():
                     continue
               except Exception as e:
                  logging.error(f"endDateTime format error: {e}")
                  continue
         brd_classification_dict[item["id"]] = item["name"]
      return brd_classification_dict

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
            1. Reason: Test should not affect running services. 
   2. `contention-classification-api/src/python_src/util/brd_classification_codes.py`
      ```python
      def get_classification_code(classification_name: str) -> Optional[int]:
         return CLASSIFICATION_CODES_BY_NAME.get(classification_name)
      ```
      1. `contention-classification-api/tests/test_brd_classification_codes.py`
         1. Issue: Unlikely
            1. Reason: Test should not affect running services. 
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
            1. Reason: Test should not affect running services. 