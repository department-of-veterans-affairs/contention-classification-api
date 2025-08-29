from typing import Any, Dict, Optional

from .lookup_tables_utilities import InitValues, read_csv_to_list


class DiagnosticCodeLookupTable:
    """
    Lookup table for mapping diagnostic codes to contention classification codes

    Attributes:
    ----------
    init_values: InitValues
        Dataclass that stores the initialization values for the lookup table stored in tehe app_config.yaml
    """

    def __init__(
        self,
        init_values: InitValues,
    ) -> None:
        self.init_values = init_values
        self.classification_code_mappings = {}
        csv_rows = read_csv_to_list(self.init_values.csv_filepath)
        for row in csv_rows:
            table_key = row[str(self.init_values.input_key)].strip().lower()
            self.classification_code_mappings[table_key] = {
                "classification_code": int(row[self.init_values.classification_code]),
                "classification_name": row[
                    self.init_values.classification_name
                ],  # note underscore different from contention LUT
            }

    def get(self, input_str: str, default_value: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        default_value = self.init_values.lut_default_value
        classification = self.classification_code_mappings.get(input_str.strip().lower(), default_value)
        return classification

    def __len__(self) -> int:
        return len(self.classification_code_mappings)


class ContentionTextLookupTable:
    """
    Maps contention text to classification code
    For mapping autosuggestion combobox values of the add disabilities page of the 526-ez form
      as well as free text entries to a classification (name and code)

    Attributes:
    ----------
    init_values: InitValues
        Dataclass that stores the initialization values for the lookup table stored in tehe app_config.yaml
    """

    def __init__(
        self,
        init_values: InitValues,
    ) -> None:
        self.init_values = init_values
        self.classification_code_mappings = {}
        csv_rows = read_csv_to_list(self.init_values.csv_filepath)
        for row in csv_rows:
            for k in self.init_values.input_key:
                if self.init_values.active_selection is not None and row[self.init_values.active_selection] == "Active":
                    table_key = row[k].strip().lower()
                    if table_key != "":
                        self.classification_code_mappings[table_key] = {
                            "classification_code": int(row[self.init_values.classification_code]),
                            "classification_name": row[self.init_values.classification_name],
                        }

    def get(self, input_str: str, default_value: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        default_value = self.init_values.lut_default_value
        classification = self.classification_code_mappings.get(input_str.strip().lower(), default_value)
        return classification

    def __len__(self) -> int:
        return len(self.classification_code_mappings)
