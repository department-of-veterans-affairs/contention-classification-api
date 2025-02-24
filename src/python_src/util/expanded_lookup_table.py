import re
from string import punctuation
from typing import Any, Dict, FrozenSet, List, Optional, Union

from .lookup_tables_utilities import InitValues, read_csv_to_list


class ExpandedLookupTable:
    """
    Lookup table to perform expanded classification lookup based on mappings between contention text and
    classification codes/names.

    Attributes:
    ----------
    init_values: InitValues
        Dataclass that stores the initialization values for the lookup table stored in tehe app_config.yaml
    common_words: list[str]
        List of common words that are removed from the lookup table and incoming contention text
    musculoskeletal_lut: dict[str, dict[str, str | int]]
        Lookup table for musculoskeletal classifications that are for single body parts:
            ex: {"keee": {"classification_code": 8997, "classification_name": "Musculoskeletal - Knee"}}
    """

    def __init__(
        self,
        init_values: InitValues,
        common_words: List[str],
        musculoskeletal_lut: Dict[str, Dict[str, Union[str, int]]],
    ) -> None:
        """
        Builds the lookup table for expanded classification using a CSV file path, plus
        additional musculoskeletal rules and removal of common words, all defined in app_config.yaml.
        """
        self.init_values = init_values
        self.common_words = common_words
        self.musculoskeletal_lookup = musculoskeletal_lut
        self.contention_text_lookup_table = self._build_lut()

    def _musculoskeletal_lookup(self) -> Dict[FrozenSet[str], Dict[str, Union[str, int]]]:
        """
        Creates a lookup table for musculoskeletal conditions with the key a frozenset.
        The musculoskeletal classifications are stored in the config file and can be added/updated there.
        """
        MUSCULOSKELETAL_LUT_SET = {}
        for k, v in self.musculoskeletal_lookup.items():
            s = frozenset(k.split())
            MUSCULOSKELETAL_LUT_SET[s] = v

        return MUSCULOSKELETAL_LUT_SET

    def _remove_spaces(self, text: str) -> str:
        return re.sub(r"\s{2,}", " ", text).strip()

    def _remove_punctuation(self, text: str) -> str:
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

    def _remove_common_words(self, text: str) -> str:
        """
        Removes common words from the lookup table contention text values
        """
        regex = re.compile(rf"\b({'|'.join(self.common_words)})\b", re.IGNORECASE)
        removed_words = re.sub(regex, " ", text)
        removed_words = self._remove_spaces(removed_words)
        return removed_words

    def _remove_numbers_single_characters(self, text: str) -> str:
        """
        Removes numbers or single character letters
        """
        regex = r"\b[a-zA-Z]{1}\b|\d"
        text = re.sub(regex, " ", text)
        text = self._remove_spaces(text)
        return text

    def _removal_pipeline(self, text: str) -> str:
        """
        Pipeline to remove all unwanted characters from the lookup table contention text values
        """
        text = self._remove_punctuation(text)
        text = self._remove_numbers_single_characters(text)
        text = self._remove_common_words(text)

        return text.lower().strip()

    def _is_in_table(
        self, term: str, row: Dict[str, str], classification_code_mappings: Dict[FrozenSet[str], Dict[str, Union[str, int]]]
    ) -> bool:
        """
        Checks if the term is already in the lookup table and if the classification code is different.
        This prevents overwriting classification codes that have already been added.

        Args:
            term (str): The term to check.
            row (dict): A row from the CSV containing classification data.
            classification_code_mappings (dict): The lookup table to check.
        """

        temp = frozenset(self._removal_pipeline(term).split())
        is_in_table = temp in classification_code_mappings
        if is_in_table:
            classification_codes_differ = classification_code_mappings[temp]["classification_code"] != int(
                row[self.init_values.classification_code]
            )
        return is_in_table and classification_codes_differ

    def _add_to_lut(
        self,
        key: str,
        row: Dict[str, str],
        classification_code_mappings: Dict[FrozenSet[str], Dict[str, Union[str, int]]],
    ) -> None:
        """
        Adds a processed key and corresponding classification data to the lookup table.
        Args:
            key (str): The string key to process and add.
            row (dict): A row from the CSV containing classification data.
            classification_code_mappings (dict): The lookup table to update.
        """
        processed_key = self._removal_pipeline(key)
        if processed_key != "":
            term_set: FrozenSet[str] = frozenset(self._removal_pipeline(key).split())
            classification_code_mappings[term_set] = {
                "classification_code": int(row[self.init_values.classification_code]),
                "classification_name": row[self.init_values.classification_name],
            }

    def _build_lut(self) -> Dict[FrozenSet[str], Dict[str, Union[str, int]]]:
        """
        Builds the lookup table using the CSV file

        This also pulls out terms in parentheses and adds the separated strings to the list and also keeping the OG term
        """
        classification_code_mappings: Dict[FrozenSet[str], Dict[str, Union[str, int]]] = {}
        csv_rows = read_csv_to_list(self.init_values.csv_filepath)
        for row in csv_rows:
            if self.init_values.active_selection is not None and row[self.init_values.active_selection] == "Active":
                for key_text in self.init_values.input_key:
                    if row[key_text]:
                        # adds the original string
                        if self._is_in_table(row[key_text], row, classification_code_mappings):
                            pass
                        else:
                            self._add_to_lut(row[key_text], row, classification_code_mappings)
        # adds the joint lookup to the table
        classification_code_mappings.update(self._musculoskeletal_lookup())

        return classification_code_mappings

    def prep_incoming_text(self, input_str: str) -> str:
        """
        Prepares the incoming text for lookup by removing common words and punctuation
        """
        input_str = input_str.strip().lower()

        for term in ["due to", "secondary to", "because of"]:
            if term in input_str:
                input_str = input_str.split(term)[0]
        input_str = self._removal_pipeline(input_str)

        return input_str

    def get(self, input_str: str, default_value: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes input string using same method as the LUT and performs the lookup

        Handles due to / secondary to conditions by pulling out first terms before
        the cause indicator

        This also process the parenthetical terms in the mappings
        """
        default_value = self.init_values.lut_default_value
        if input_str == "loss of teeth due to bone loss":
            return {
                "classification_code": 8967,
                "classification_name": "Dental and Oral",
            }

        input_str = self.prep_incoming_text(input_str)

        input_str_lookup = frozenset(input_str.split())
        classification = self.contention_text_lookup_table.get(input_str_lookup, default_value)
        return classification

    def __len__(self) -> int:
        """
        Returns length of the LUT
        """
        return len(self.contention_text_lookup_table)
