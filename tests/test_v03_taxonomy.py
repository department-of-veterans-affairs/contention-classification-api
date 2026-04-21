"""
Integration tests for terms newly introduced in v0.3 of the "CC Taxonomy master" csv.

These tests simulate a POST to /expanded-contention-classification and verify
classification_code, classification_name, is_in_dropdown, and is_lookup_table_match
"""

from typing import List, Optional, Tuple
from unittest.mock import MagicMock, patch

from fastapi import Request
from starlette.datastructures import Headers

from src.python_src.pydantic_models import Contention, VaGovClaim
from src.python_src.util.classifier_utilities import classify_contention

EXPANDED_REQUEST = Request(
    scope={
        "type": "http",
        "method": "POST",
        "path": "/expanded-contention-classification",
        "headers": Headers(),
    }
)

# Each entry: (contention_text, expected_code, expected_name, is_in_dropdown, is_lookup_table_match)
ContentionExpectation = Tuple[str, Optional[int], Optional[str], bool, bool]


def _assert_contention_log(
    mock_log: MagicMock,
    expectations: List[ContentionExpectation],
) -> None:
    """Build a claim from the given expectations and assert logged values for each contention."""
    claim = VaGovClaim(
        claim_id=44,
        form526_submission_id=55,
        contentions=[Contention(contention_text=text, contention_type="NEW") for text, *_ in expectations],
    )
    for contention_text, expected_code, expected_name, expected_in_dropdown, expected_lut_match in expectations:
        mock_log.reset_mock()
        classify_contention(Contention(contention_text=contention_text, contention_type="NEW"), claim, EXPANDED_REQUEST)
        logged = mock_log.call_args[0][0]
        assert logged["is_in_dropdown"] is expected_in_dropdown, f"{contention_text!r}: unexpected is_in_dropdown"
        assert logged["is_lookup_table_match"] is expected_lut_match, f"{contention_text!r}: unexpected is_lookup_table_match"
        assert logged["classification_code"] == expected_code, f"{contention_text!r}: unexpected classification_code"
        assert logged["classification_name"] == expected_name, f"{contention_text!r}: unexpected classification_name"


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_new_autosuggestion_terms_are_classified_and_in_dropdown(mock_log: MagicMock) -> None:
    """
    Tests that terms listed under the "Main condition/term" column are classified
    and have is_in_dropdown=True and is_lookup_table_match=True.
    """
    _assert_contention_log(
        mock_log,
        [
            ("Alzheimer's disease", 8989, "Mental Disorders", True, True),
            ("ALS (amyotrophic lateral sclerosis)", 9007, "Neurological other System", True, True),
            ("sciatica (sciatic nerve radiculopathy), right", 9006, "Neurological - Cranial/Peripheral Nerves", True, True),
            ("granulomatous rhinitis", 9012, "Respiratory", True, True),
            ("bruxism (teeth grinding)", 249481, "Dental and Oral - Musculoskeletal", True, True),
            ("insomnia", 8989, "Mental Disorders", True, True),
        ],
    )


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_new_synonyms_are_classified_but_not_found_in_dropdown(mock_log: MagicMock) -> None:
    """
    Terms like 'menieres', 'trench foot', and 'alzheimers' are present as synonyms to
    known conditions, however are not exact autosuggestion dropdown values.
    Correspondingly, we expect:
    - classification_code and classification_name are found
    - is_in_dropdown = false
    - is_lookup_table_match = true
    """
    _assert_contention_log(
        mock_log,
        [
            ("menieres", 8969, "Ear Disease and Other Sense Organs", False, True),
            ("trench foot", 8943, "Cold Injury Residuals", False, True),
            ("alzheimers", 8989, "Mental Disorders", False, True),
        ],
    )


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_frozen_shoulder_synonyms_are_classified_but_not_in_dropdown(mock_log: MagicMock) -> None:
    """
    Synonyms for 'frozen shoulder (adhesive capsulitis)' should
    resolve to the correct classification via the expanded lookup, but not be
    found in the dropdown.
    """
    _assert_contention_log(
        mock_log,
        [
            ("frozen shoulder", 9002, "Musculoskeletal - Shoulder", False, True),
            ("adhesive capsulitis", 9002, "Musculoskeletal - Shoulder", False, True),
            ("scapulohumeral articulation, ankylosis", 9002, "Musculoskeletal - Shoulder", False, True),
            ("ankylosis in shoulder", 9002, "Musculoskeletal - Shoulder", False, True),
        ],
    )


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_frozen_shoulder_laterality_terms_are_in_dropdown_and_classified(mock_log: MagicMock) -> None:
    """
    The laterality variants of 'frozen shoulder (adhesive capsulitis)' are exact
    autosuggestion dropdown terms and should be fully classified with
    is_in_dropdown=True and is_lookup_table_match=True.
    """
    _assert_contention_log(
        mock_log,
        [
            ("frozen shoulder (adhesive capsulitis), left", 9002, "Musculoskeletal - Shoulder", True, True),
            ("frozen shoulder (adhesive capsulitis), bilateral", 9002, "Musculoskeletal - Shoulder", True, True),
            ("frozen shoulder (adhesive capsulitis), right", 9002, "Musculoskeletal - Shoulder", True, True),
        ],
    )
