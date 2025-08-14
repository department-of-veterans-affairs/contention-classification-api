# SHA-256 Verification for ML Classifier Files

This document describes the SHA-256 verification functionality added to the ML classifier component of the contention classification API.

## Overview

SHA-256 verification has been added to ensure the integrity and authenticity of ML model files downloaded from S3. This security measure helps prevent the use of corrupted or tampered model files.

## Configuration

The SHA verification is configured in `app_config.yaml` under the `ml_classifier.verification` section:

```yaml
ml_classifier:
  verification:
    enable_sha_check: true
    expected_sha256:
      model: 'af53814d71a48518c2d8c47eab8db9adf2ba40249d6f634b4f059268be750b8e'
      vectorizer: '33052586943574c34884371d9f987e440e7a5d3cb5e85bb8a19fd334f1f610c5'
    chunk_size: 4096
```

### Configuration Parameters

- **`enable_sha_check`**: Boolean flag to enable/disable SHA verification
- **`expected_sha256.model`**: Expected SHA-256 hash for the ONNX model file
- **`expected_sha256.vectorizer`**: Expected SHA-256 hash for the vectorizer pickle file
- **`chunk_size`**: Chunk size in bytes for reading files during hash calculation (default: 4096)

## How It Works

### 1. On Application Startup

When the application starts, the system:

1. Checks if model files exist locally
2. If SHA verification is enabled and files exist:
   - Calculates SHA-256 of existing files
   - Compares with expected values from configuration
   - If verification fails, removes invalid files and marks for re-download
3. Downloads missing or invalid files from S3
4. Verifies downloaded files against expected SHA-256 values
5. Removes and raises an exception if downloaded files fail verification

### 2. During File Download

When downloading files from S3:

1. Files are downloaded to the local models directory
2. SHA-256 is calculated for each downloaded file
3. Hash is compared against expected value from configuration
4. If verification fails:
   - The invalid file is immediately removed
   - An exception is raised to prevent loading compromised files

## Security Benefits

- **Integrity Verification**: Ensures files haven't been corrupted during transfer
- **Authenticity Check**: Verifies files match expected versions
- **Tamper Detection**: Identifies if files have been modified
- **Automatic Cleanup**: Removes invalid files to prevent accidental use

## Expected SHA-256 Values

The current expected SHA-256 values are:

- **Model file** (`LR_tfidf_fit_model_20250623_151434.onnx`):
  `af53814d71a48518c2d8c47eab8db9adf2ba40249d6f634b4f059268be750b8e`

- **Vectorizer file** (`LR_tfidf_fit_False_features_20250521_20250623_151434_vectorizer.pkl`):
  `33052586943574c34884371d9f987e440e7a5d3cb5e85bb8a19fd334f1f610c5`

## Functions Added

### `calculate_file_sha256(file_path: str, chunk_size: int = 4096) -> str`

Calculates the SHA-256 hash of a file using chunked reading for memory efficiency.

**Parameters:**
- `file_path`: Path to the file to hash
- `chunk_size`: Size of chunks to read (default: 4096 bytes)

**Returns:** Hexadecimal SHA-256 hash string

### `verify_file_sha256(file_path: str, expected_sha256: str, chunk_size: int = 4096) -> bool`

Verifies that a file's SHA-256 matches an expected value.

**Parameters:**
- `file_path`: Path to the file to verify
- `expected_sha256`: Expected SHA-256 hash (hexadecimal string)
- `chunk_size`: Size of chunks to read (default: 4096 bytes)

**Returns:** `True` if verification succeeds, `False` otherwise

### Enhanced `download_ml_models_from_s3(model_file: str, vectorizer_file: str) -> tuple[str, str]`

The existing download function has been enhanced to include SHA verification:

- Downloads files from S3 as before
- Performs SHA-256 verification if enabled
- Removes and raises exception for files that fail verification
- Provides detailed logging for all verification steps

## Logging

The SHA verification process generates detailed logs:

- `INFO`: Successful verification, download progress
- `ERROR`: Verification failures, file removal actions
- `WARNING`: When existing files fail verification and need re-download

## Error Handling

If SHA verification fails:

1. **For existing files**: Files are removed and marked for re-download
2. **For downloaded files**: Files are immediately removed and an exception is raised
3. **Application continues**: Only with verified files or fails to initialize ML classifier

## Updating SHA Values

When ML model files are updated:

1. Update the expected SHA-256 values in `app_config.yaml`
2. The application will automatically detect the mismatch and download new files
3. Verify the new SHA-256 values match the updated configuration

## Disabling SHA Verification

To disable SHA verification (not recommended for production):

```yaml
ml_classifier:
  verification:
    enable_sha_check: false
```

When disabled, the system will still download missing files but won't verify their integrity.
