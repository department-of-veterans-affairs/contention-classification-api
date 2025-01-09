import csv
import os
import re
from string import punctuation
from typing import List

from .app_utilities import load_config

app_config = load_config(os.path.join(os.path.dirname(__file__), "app_config.yaml"))

LUT_DEFAULT_VALUE = app_config["lut_default_value"]
COMMON_WORDS = app_config["common_words"]
MUSCULOSKELETAL_LUT = app_config["musculoskeletal_lut"]
contention_lut_csv_filename = (
    f"{app_config['condition_dropdown_table']['filename']} {app_config['condition_dropdown_table']['version_number']}.csv"
)
filepath = os.path.join(os.path.dirname(__file__), "data", "condition_dropdown_lookup_table", contention_lut_csv_filename)


class ExpandedLookupTable:
    """
    This parses the lookup table to use sets and remove common words and punctuations
    """

    def __init__(self, key_text: str, classification_code: int, classification_name: str):
        """
        builds the lookup table using class methods
        """
        self.key_text = key_text
        self.classification_code = classification_code
        self.classification_name = classification_name
        self.contention_text_lookup_table = self._build_lut()

    def _musculoskeletal_lookup(self):
        """
        Creates a lookup table for musculoskeletal conditions with the key a frozenset.
        The musculoskeletal classifications are stored in the config file and can be added/updated there.
        """
        MUSCULOSKELETAL_LUT_LUT_SET = {}
        for k, v in MUSCULOSKELETAL_LUT.items():
            s = frozenset(k.split())
            MUSCULOSKELETAL_LUT_LUT_SET[s] = v

        return MUSCULOSKELETAL_LUT_LUT_SET

    def _remove_spaces(self, text):
        return re.sub(r"\s{2,}", " ", text).strip()

    def _remove_punctuation(self, text):
        """
        Removes puncutation from the lookup table contention text and any spaces of 2 or more
        """
        # removes apostrophes to capture if it is 's or s' and replaces with empty character
        removed_apostrophe = text.replace("'", "")

        # remove all other punctuation and replace with " "
        removed_punc = re.sub(rf"[{punctuation}]", " ", removed_apostrophe)

        # remove double spaces and replace with single space
        removed_punc_spaces = self._remove_spaces(removed_punc)

        return removed_punc_spaces.strip()

    def _remove_common_words(self, text, common_words: List[str] = COMMON_WORDS):
        """
        Removes common words from the lookup table contention text values
        """
        regex = re.compile(rf'\b({"|".join(COMMON_WORDS)})\b', re.IGNORECASE)
        removed_words = re.sub(regex, " ", text)
        removed_words = self._remove_spaces(removed_words)
        return removed_words

    def _remove_numbers_single_characters(self, text):
        """
        Removes numbers or single character letters
        """
        regex = r"\b[a-zA-Z]{1}\b|\d"
        text = re.sub(regex, " ", text)
        text = self._remove_spaces(text)
        return text

    def _removal_pipeline(self, text):
        """
        Pipeline to remove all unwanted characters from the lookup table contention text values
        """
        text = self._remove_punctuation(text)
        text = self._remove_numbers_single_characters(text)
        text = self._remove_common_words(text)

        return text.lower().strip()

    def _build_lut(self):
        """
        Builds the lookup table using the CSV file

        This also pulls out terms in parentheses and adds the separated strings to the list and also keeping the OG term
        """
        classification_code_mappings = {}
        with open(filepath) as fh:
            csv_reader = csv.DictReader(fh)
            for row in csv_reader:
                if "(" in row[self.key_text]:
                    parenthetical_terms = re.findall(r"\((.*?)\)", row[self.key_text])
                    ls_terms = [term for term in parenthetical_terms]
                    removed_parenthetical = [re.sub(r"\(.*?\)", "", row[self.key_text])]
                    ls_terms.extend(removed_parenthetical)
                    for t in ls_terms:
                        k = self._removal_pipeline(t)
                        if k != "":
                            k = frozenset(k.split())
                            classification_code_mappings[k] = {
                                "classification_code": int(row[self.classification_code]),
                                "classification_name": row[self.classification_name],
                            }

                # adds the original string
                k = self._removal_pipeline(row[self.key_text])
                k = frozenset(k.split())
                classification_code_mappings[k] = {
                    "classification_code": int(row[self.classification_code]),
                    "classification_name": row[self.classification_name],
                }
            # adds the joint lookup to the table
            classification_code_mappings.update(self._musculoskeletal_lookup())

        return classification_code_mappings

    def prep_incoming_text(self, input_str: str):
        """
        Prepares the incoming text for lookup by removing common words and punctuation
        """
        input_str = input_str.strip().lower()

        for term in ["due to", "secondary to", "because of"]:
            if term in input_str:
                input_str = input_str.split(term)[0]
        input_str = self._removal_pipeline(input_str)

        return input_str

    def get(self, input_str: str, default_value=LUT_DEFAULT_VALUE):
        """
        Processes input string using same method as the LUT and performs the lookup

        Handles due to / secondary to conditions by pulling out first terms before
        the cause indicator

        This also process the parenthetical terms in the mappings
        """
        if input_str == "loss of teeth due to bone loss":
            return {
                "classification_code": 8967,
                "classification_name": "Dental and Oral",
            }

        input_str = self.prep_incoming_text(input_str)

        input_str_lookup = frozenset(input_str.split())
        classification = self.contention_text_lookup_table.get(input_str_lookup, default_value)
        return classification

    def __len__(self):
        """
        Returns length of the LUT
        """
        return len(self.contention_text_lookup_table)
