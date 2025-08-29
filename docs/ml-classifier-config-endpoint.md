# ML Classifier Configuration Endpoint

This document describes the new ML Classifier Configuration endpoint that allows dynamic updating of ML model files and reinitialization of the classifier with the latest data.

## Endpoint: `/ml-classifier-config`

**Method:** POST

**Description:** Updates the ML classifier configuration and reinitializes the classifier with new model files from S3.

### Request Body

The endpoint accepts a JSON request with the following optional fields:

```json
{
  "model_filename": "string",           // New model filename (optional)
  "vectorizer_filename": "string",      // New vectorizer filename (optional)
  "s3_model_key": "string",            // New S3 key for model file (optional)
  "s3_vectorizer_key": "string",       // New S3 key for vectorizer file (optional)
  "force_download": false,             // Force re-download even if files exist (optional, default: false)
  "expected_model_sha256": "string",   // Expected SHA256 for model verification (optional)
  "expected_vectorizer_sha256": "string" // Expected SHA256 for vectorizer verification (optional)
}
```

**Note:** At least one parameter must be provided in the request.

### Response

The endpoint returns a JSON response with the following structure:

```json
{
  "success": true,                     // Whether the update was successful
  "message": "string",                 // Description of the result
  "previous_version": {                // Previous model/vectorizer versions (if available)
    "model": "string",
    "vectorizer": "string"
  },
  "new_version": {                     // New model/vectorizer versions (if successful)
    "model": "string",
    "vectorizer": "string"
  },
  "files_updated": ["string"]          // List of files that were updated ("model", "vectorizer")
}
```

### Use Cases

#### 1. Update Model Files with New Versions

Update both model and vectorizer files with new versions:

```bash
curl -X POST "http://localhost:8000/ml-classifier-config" \
  -H "Content-Type: application/json" \
  -d '{
    "model_filename": "LR_tfidf_fit_model_20250829_120000.onnx",
    "vectorizer_filename": "LR_tfidf_fit_False_features_20250829_120000_vectorizer.pkl",
    "s3_model_key": "models/LR_tfidf_fit_model_20250829_120000.onnx",
    "s3_vectorizer_key": "models/LR_tfidf_fit_False_features_20250829_120000_vectorizer.pkl",
    "expected_model_sha256": "abc123...",
    "expected_vectorizer_sha256": "def456..."
  }'
```

#### 2. Force Re-download of Existing Files

Force re-download and reinitialize with existing configuration:

```bash
curl -X POST "http://localhost:8000/ml-classifier-config" \
  -H "Content-Type: application/json" \
  -d '{
    "force_download": true
  }'
```

#### 3. Update Only SHA Checksums

Update expected SHA checksums without changing filenames:

```bash
curl -X POST "http://localhost:8000/ml-classifier-config" \
  -H "Content-Type: application/json" \
  -d '{
    "expected_model_sha256": "new_sha_checksum_here",
    "expected_vectorizer_sha256": "new_vectorizer_sha_here"
  }'
```

#### 4. Update S3 Keys Only

Update S3 object keys without changing local filenames:

```bash
curl -X POST "http://localhost:8000/ml-classifier-config" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_model_key": "new_path/model_file.onnx",
    "s3_vectorizer_key": "new_path/vectorizer_file.pkl"
  }'
```

### Error Responses

The endpoint returns appropriate HTTP status codes:

- **400 Bad Request:** When no configuration parameters are provided
- **500 Internal Server Error:** When the update fails (download error, initialization error, etc.)

Example error response:
```json
{
  "detail": "Failed to download ML models: S3 bucket not accessible"
}
```

### Security Considerations

- **SHA Verification:** The endpoint respects the SHA-256 verification settings in the application configuration
- **Environment Variables:** SHA checksums can be overridden by environment variables (`ML_MODEL_SHA256`, `ML_VECTORIZER_SHA256`)
- **File Validation:** All downloaded files are verified before the classifier is reinitialized
- **Atomic Updates:** If any part of the update process fails, the previous classifier remains active

### Logging

The endpoint logs important events:

- Configuration updates
- File downloads
- Classifier reinitialization
- Errors and exceptions

Example log entry:
```json
{
  "action": "ml_classifier_config_update",
  "success": true,
  "files_updated": ["model", "vectorizer"],
  "previous_version": {"model": "old_model.onnx", "vectorizer": "old_vectorizer.pkl"},
  "new_version": {"model": "new_model.onnx", "vectorizer": "new_vectorizer.pkl"}
}
```

### Dependencies

This endpoint relies on:

- S3 access for downloading model files
- Proper AWS credentials and permissions
- Valid app configuration (`app_config.yaml`)
- ONNX runtime for model loading
- scikit-learn for vectorizer loading

### Integration with Existing Endpoints

After a successful configuration update:

- The `/health` endpoint will reflect the new classifier status
- The `/ml-contention-classification` endpoint will use the new classifier
- The `/hybrid-contention-classification` endpoint will use the new classifier for supplemental classification
- All existing functionality remains unchanged

### Version Tracking

The endpoint tracks model versions by extracting information from filenames. The version information is included in the response to help with auditing and troubleshooting.
