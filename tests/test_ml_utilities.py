"""Tests for ml_utilities module."""

from unittest.mock import MagicMock, patch

from src.python_src.util.ml_utilities import get_model_file_paths, load_ml_classifier


class TestGetModelFilePaths:
    """Test cases for get_model_file_paths function."""

    def test_get_model_file_paths_basic(self) -> None:
        """Test basic functionality of get_model_file_paths."""
        mock_config = {
            "ml_classifier": {
                "storage": {"local_directory": "models/"},
                "files": {"model_filename": "test_model.onnx", "vectorizer_filename": "test_vectorizer.pkl"},
            }
        }

        model_file, vectorizer_file = get_model_file_paths(mock_config)

        # Check that paths are constructed correctly
        assert model_file.endswith("models/test_model.onnx")
        assert vectorizer_file.endswith("models/test_vectorizer.pkl")
        assert "util" in model_file  # Should include the util directory in path

    def test_get_model_file_paths_different_directory(self) -> None:
        """Test get_model_file_paths with different directory."""
        mock_config = {
            "ml_classifier": {
                "storage": {"local_directory": "ml_models/"},
                "files": {"model_filename": "classifier.onnx", "vectorizer_filename": "tfidf.pkl"},
            }
        }

        model_file, vectorizer_file = get_model_file_paths(mock_config)

        assert model_file.endswith("ml_models/classifier.onnx")
        assert vectorizer_file.endswith("ml_models/tfidf.pkl")

    def test_get_model_file_paths_nested_structure(self) -> None:
        """Test get_model_file_paths with nested directory structure."""
        mock_config = {
            "ml_classifier": {
                "storage": {"local_directory": "data/models/v1/"},
                "files": {"model_filename": "lr_model.onnx", "vectorizer_filename": "vectorizer_v1.pkl"},
            }
        }

        model_file, vectorizer_file = get_model_file_paths(mock_config)

        assert "data/models/v1/lr_model.onnx" in model_file
        assert "data/models/v1/vectorizer_v1.pkl" in vectorizer_file


class TestLoadMLClassifier:
    """Test cases for load_ml_classifier function."""

    @patch("src.python_src.util.ml_utilities.MLClassifier")
    @patch("src.python_src.util.ml_utilities.os.path.exists")
    @patch("src.python_src.util.ml_utilities.os.makedirs")
    def test_load_ml_classifier_files_exist_no_verification(
        self, mock_makedirs: MagicMock, mock_exists: MagicMock, mock_classifier: MagicMock
    ) -> None:
        """Test loading classifier when files exist and verification is disabled."""
        mock_exists.return_value = True
        mock_classifier_instance = MagicMock()
        mock_classifier.return_value = mock_classifier_instance

        mock_config = {
            "ml_classifier": {
                "storage": {"local_directory": "models/"},
                "files": {"model_filename": "test_model.onnx", "vectorizer_filename": "test_vectorizer.pkl"},
                "integrity_verification": {"enabled": False},
            }
        }

        result = load_ml_classifier(mock_config)

        assert result == mock_classifier_instance
        mock_makedirs.assert_called_once()
        mock_classifier.assert_called_once()

    @patch("src.python_src.util.ml_utilities.download_ml_models_from_s3")
    @patch("src.python_src.util.ml_utilities.MLClassifier")
    @patch("src.python_src.util.ml_utilities.os.path.exists")
    @patch("src.python_src.util.ml_utilities.os.makedirs")
    def test_load_ml_classifier_files_missing(
        self,
        mock_makedirs: MagicMock,
        mock_exists: MagicMock,
        mock_classifier: MagicMock,
        mock_download: MagicMock,
    ) -> None:
        """Test loading classifier when files are missing and need download."""
        # First call (check if files exist) returns False, second call (after download) returns True
        mock_exists.side_effect = [False, True, True]
        mock_classifier_instance = MagicMock()
        mock_classifier.return_value = mock_classifier_instance

        mock_config = {
            "ml_classifier": {
                "storage": {"local_directory": "models/"},
                "files": {"model_filename": "test_model.onnx", "vectorizer_filename": "test_vectorizer.pkl"},
                "integrity_verification": {"enabled": False},
            }
        }

        result = load_ml_classifier(mock_config)

        assert result == mock_classifier_instance
        mock_download.assert_called_once()
        mock_classifier.assert_called_once()

    @patch("src.python_src.util.ml_utilities.verify_file_sha256")
    @patch("src.python_src.util.ml_utilities.MLClassifier")
    @patch("src.python_src.util.ml_utilities.os.path.exists")
    @patch("src.python_src.util.ml_utilities.os.makedirs")
    def test_load_ml_classifier_sha_verification_success(
        self,
        mock_makedirs: MagicMock,
        mock_exists: MagicMock,
        mock_classifier: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        """Test loading classifier with successful SHA verification."""
        mock_exists.return_value = True
        mock_verify.return_value = True
        mock_classifier_instance = MagicMock()
        mock_classifier.return_value = mock_classifier_instance

        mock_config = {
            "ml_classifier": {
                "storage": {"local_directory": "models/"},
                "files": {"model_filename": "test_model.onnx", "vectorizer_filename": "test_vectorizer.pkl"},
                "integrity_verification": {
                    "enabled": True,
                    "hash_config": {"chunk_size_bytes": 4096},
                    "expected_checksums": {"model": "abcd1234", "vectorizer": "efgh5678"},
                },
            }
        }

        result = load_ml_classifier(mock_config)

        assert result == mock_classifier_instance
        assert mock_verify.call_count == 2  # Called for both model and vectorizer
        mock_classifier.assert_called_once()

    @patch("src.python_src.util.ml_utilities.verify_file_sha256")
    @patch("src.python_src.util.ml_utilities.download_ml_models_from_s3")
    @patch("src.python_src.util.ml_utilities.MLClassifier")
    @patch("src.python_src.util.ml_utilities.os.remove")
    @patch("src.python_src.util.ml_utilities.os.path.exists")
    @patch("src.python_src.util.ml_utilities.os.makedirs")
    def test_load_ml_classifier_sha_verification_failure(
        self,
        mock_makedirs: MagicMock,
        mock_exists: MagicMock,
        mock_remove: MagicMock,
        mock_classifier: MagicMock,
        mock_download: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        """Test loading classifier with failed SHA verification triggering re-download."""
        # Files exist initially, then exist after download
        mock_exists.side_effect = [True, True, True, True, True, True]
        mock_verify.side_effect = [False, True]  # First file fails, second succeeds, then re-download
        mock_classifier_instance = MagicMock()
        mock_classifier.return_value = mock_classifier_instance

        mock_config = {
            "ml_classifier": {
                "storage": {"local_directory": "models/"},
                "files": {"model_filename": "test_model.onnx", "vectorizer_filename": "test_vectorizer.pkl"},
                "integrity_verification": {
                    "enabled": True,
                    "hash_config": {"chunk_size_bytes": 4096},
                    "expected_checksums": {"model": "abcd1234", "vectorizer": "efgh5678"},
                },
            }
        }

        result = load_ml_classifier(mock_config)

        assert result == mock_classifier_instance
        mock_remove.assert_called_once()  # Invalid file should be removed
        mock_download.assert_called_once()  # Should trigger re-download
        mock_classifier.assert_called_once()


def test_get_model_file_paths() -> None:
    """Test get_model_file_paths function with sample config."""
    sample_config = {
        "ml_classifier": {
            "storage": {"local_directory": "models/"},
            "files": {"model_filename": "sample_model.onnx", "vectorizer_filename": "sample_vectorizer.pkl"},
        }
    }

    model_path, vectorizer_path = get_model_file_paths(sample_config)

    assert isinstance(model_path, str)
    assert isinstance(vectorizer_path, str)
    assert model_path.endswith("models/sample_model.onnx")
    assert vectorizer_path.endswith("models/sample_vectorizer.pkl")
    assert model_path != vectorizer_path
