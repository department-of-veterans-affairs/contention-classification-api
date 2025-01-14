from unittest.mock import patch

from fastapi.testclient import TestClient

from src.python_src.util.app_utilities import dropdown_expanded_table_inits, load_config
from src.python_src.util.expanded_lookup_table import ExpandedLookupTable

app_config = load_config("src/python_src/util/app_config.yaml")

TEST_LUT = ExpandedLookupTable(
    init_values=dropdown_expanded_table_inits,
    common_words=app_config["common_words"],
    musculoskeletal_lut=app_config["musculoskeletal_lut"],
)


def test_remove_punctuation_within_string():
    """
    Test the remove punctuation function
    """
    text = "This is a test, with punctuation."
    expected = "This is a test with punctuation"

    assert TEST_LUT._remove_punctuation(text) == expected


def test_remove_punctuation_against_words():
    text = "This (a, string) is another => hopefully works!!"
    expected = "This a string is another hopefully works"
    assert TEST_LUT._remove_punctuation(text) == expected


def test_remove_spaces():
    text = "  This i       is a test with a     lot of spaces.    "
    expected = "This i is a test with a lot of spaces"
    assert TEST_LUT._remove_punctuation(text) == expected


def test_remove_common_words_normal():
    text = "string of words and common words"
    expected = "string words common words"
    assert TEST_LUT._remove_common_words(text) == expected


def test_does_not_remove_inside_words():
    text = "officially land lore tin"
    expected = "officially land lore tin"
    assert TEST_LUT._remove_common_words(text) == expected


def test_remove_common_words_ends_of_strings():
    text = "and this string or"
    expected = "string"
    assert TEST_LUT._remove_common_words(text) == expected


def test_get_lookup_autosuggestion():
    test_string = "tinnitus (ringing or hissing in ears)"
    expected = {
        "classification_code": 3140,
        "classification_name": "Hearing Loss",
    }
    assert TEST_LUT.get(test_string) == expected


def test_get_lookup_free_text():
    test_string = "athletes foot (tinea pedis)"
    expected = {
        "classification_code": 9016,
        "classification_name": "Skin",
    }
    assert TEST_LUT.get(test_string) == expected


def test_get_lookup_free_text_second():
    test_string = "ringing in ears"
    expected = {
        "classification_code": 3140,
        "classification_name": "Hearing Loss",
    }
    assert TEST_LUT.get(test_string) == expected


def test_lookup_with_out_side_typos():
    test_string = "ACL TEAR (ANTERIOR CRUCIATE LIGAMENT      TEAR "
    expected = {
        "classification_code": 8997,
        "classification_name": "Musculoskeletal - Knee",
    }
    assert TEST_LUT.get(test_string) == expected


def test_remove_digits():
    test_str = "123 some 789 condition 0456"
    expected = "some condition"
    assert TEST_LUT._remove_numbers_single_characters(test_str) == expected


def test_remove_single_letters():
    test_str = "pain in a leg r b"
    expected = "pain in leg"
    assert TEST_LUT._remove_numbers_single_characters(test_str) == expected


def test_full_removal_pipeline():
    test_str = "I have pain in 3 areas in the r side of body!"
    expected = "areas body"
    assert TEST_LUT._removal_pipeline(test_str) == expected


def test_remove_common_words():
    test_str = " ".join(app_config["common_words"])
    expected = ""
    assert TEST_LUT._remove_common_words(test_str).strip() == expected


def test_removed_parentheses():
    test_str = "acl tear, left"
    expected = {
        "classification_code": 8997,
        "classification_name": "Musculoskeletal - Knee",
    }
    assert TEST_LUT.get(test_str) == expected


@patch("src.python_src.util.expanded_lookup_table.ExpandedLookupTable._removal_pipeline")
def test_prep_incoming_text_cause(mock_removal_pipeline):
    test_str = "acl tear, due to something"
    TEST_LUT.prep_incoming_text(test_str)
    mock_removal_pipeline.assert_called_once_with("acl tear, ")


@patch("src.python_src.util.expanded_lookup_table.ExpandedLookupTable._removal_pipeline")
def test_prep_incoming_text_non_cause(mock_removal_pipeline):
    test_str = "acl tear in my right knee"
    TEST_LUT.prep_incoming_text(test_str)
    mock_removal_pipeline.assert_called_once_with(test_str)


def test_lookup_cause_included():
    test_str = [
        "migraines (headaches), due to something",
        "Tinnitus secondary to hearing loss",
        "free text due to something else",
        "Due to something 1, condition 2",
        "loss of teeth due to bone loss",
        "bilateral feet condition",
    ]

    assert TEST_LUT.get(test_str[0]) == {
        "classification_code": 9007,
        "classification_name": "Neurological other System",
    }
    assert TEST_LUT.get(test_str[1]) == {
        "classification_code": 3140,
        "classification_name": "Hearing Loss",
    }
    assert TEST_LUT.get(test_str[2]) == {
        "classification_code": None,
        "classification_name": None,
    }
    assert TEST_LUT.get(test_str[3]) == {
        "classification_code": None,
        "classification_name": None,
    }
    assert TEST_LUT.get(test_str[4]) == {
        "classification_code": 8967,
        "classification_name": "Dental and Oral",
    }
    assert TEST_LUT.get(test_str[5]) == {
        "classification_code": 8994,
        "classification_name": "Musculoskeletal - Foot",
    }


def test_api_endpoint(client: TestClient):
    json_post_data = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "contentions": [
            {
                "contention_text": "PTSD (post-traumatic stress disorder)",
                "contention_type": "NEW",
            },
            {
                "contention_text": "",
                "contention_type": "INCREASE",
                "diagnostic_code": 5012,
            },
            {"contention_text": "anxiety condition", "contention_type": "new"},
            {"contention_text": "acl tear", "contention_type": "new"},
            {"contention_text": "totally free text", "contention_type": "new"},
            {"contention_text": "neuropathy in my hand", "contention_type": "new"},
            {
                "contention_text": "knee pain due to something else entirely",
                "contention_type": "new",
            },
            {
                "contention_text": "left ankle condition",
                "contention_type": "increase",
                "diagnostic_code": 1000,
            },
        ],
    }
    response = client.post("/expanded-contention-classification", json=json_post_data)
    assert response.status_code == 200
    assert response.json() == {
        "contentions": [
            {
                "classification_code": 8989,
                "classification_name": "Mental Disorders",
                "diagnostic_code": None,
                "contention_type": "NEW",
            },
            {
                "classification_code": 8940,
                "classification_name": "Cancer - Musculoskeletal - Other",
                "diagnostic_code": 5012,
                "contention_type": "INCREASE",
            },
            {
                "classification_code": 8989,
                "classification_name": "Mental Disorders",
                "diagnostic_code": None,
                "contention_type": "new",
            },
            {
                "classification_code": 8997,
                "classification_name": "Musculoskeletal - Knee",
                "diagnostic_code": None,
                "contention_type": "new",
            },
            {
                "classification_code": None,
                "classification_name": None,
                "diagnostic_code": None,
                "contention_type": "new",
            },
            {
                "classification_code": None,
                "classification_name": None,
                "diagnostic_code": None,
                "contention_type": "new",
            },
            {
                "classification_code": 8997,
                "classification_name": "Musculoskeletal - Knee",
                "diagnostic_code": None,
                "contention_type": "new",
            },
            {
                "classification_code": 8991,
                "classification_name": "Musculoskeletal - Ankle",
                "diagnostic_code": 1000,
                "contention_type": "increase",
            },
        ],
        "claim_id": 100,
        "form526_submission_id": 500,
        "is_fully_classified": False,
        "num_processed_contentions": 8,
        "num_classified_contentions": 6,
    }
