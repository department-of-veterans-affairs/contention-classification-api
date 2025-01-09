import csv
import os

from .app_utilities import load_config

app_config = load_config(os.path.join(os.path.dirname(__file__), "app_config.yaml"))

dc_table_name = (
    f"{app_config['diagnostic_code_table']['filename']} {app_config['diagnostic_code_table']['version_number']}.csv"
)
contention_lut_csv_filename = (
    f"{app_config['condition_dropdown_table']['filename']} {app_config['condition_dropdown_table']['version_number']}.csv"
)
LUT_DEFAULT_VALUE = app_config["lut_default_value"]


class DiagnosticCodeLookupTable:
    """
    Lookup table for mapping diagnostic codes to contention classification codes
    """

    CSV_FILEPATH = os.path.join(os.path.dirname(__file__), "data", "dc_lookup_table", dc_table_name)
    input_key = app_config["diagnostic_code_table"]["input_key"]
    classification_code = app_config["diagnostic_code_table"]["classification_code"]
    classification_name = app_config["diagnostic_code_table"]["classification_name"]

    def __init__(self):
        self.classification_code_mappings = {}
        with open(self.CSV_FILEPATH, "r") as fh:
            csv_reader = csv.DictReader(fh)
            for row in csv_reader:
                table_key = row[str(self.input_key)].strip().lower()
                self.classification_code_mappings[table_key] = {
                    "classification_code": int(row[self.classification_code]),
                    "classification_name": row[self.classification_name],  # note underscore different from contention LUT
                }

    def get(self, input_key: int, default_value=LUT_DEFAULT_VALUE):
        classification = self.classification_code_mappings.get(str(input_key), default_value)
        return classification

    def __len__(self):
        return len(self.classification_code_mappings)


class ContentionTextLookupTable:
    """
    Maps contention text to classification code
    For mapping autosuggestion combobox values of the add disabilities page of the 526-ez form
      as well as free text entries to a classification (name and code)
    """

    CSV_FILEPATH = os.path.join(
        os.path.dirname(__file__),
        "data",
        "condition_dropdown_lookup_table",
        contention_lut_csv_filename,
    )
    input_key = app_config["condition_dropdown_table"]["input_key"]
    classification_code = app_config["condition_dropdown_table"]["classification_code"]
    classification_name = app_config["condition_dropdown_table"]["classification_name"]
    classification_code_mappings = {}

    def __init__(self):
        with open(self.CSV_FILEPATH, "r") as fh:
            csv_reader = csv.DictReader(fh)
            for row in csv_reader:
                table_key = row[self.input_key].strip().lower()
                self.classification_code_mappings[table_key] = {
                    "classification_code": int(row[self.classification_code]),
                    "classification_name": row[self.classification_name],
                }

    def get(self, input_str: str, default_value=LUT_DEFAULT_VALUE):
        input_str = input_str.strip().lower()
        classification = self.classification_code_mappings.get(input_str, default_value)
        return classification

    def __len__(self):
        return len(self.classification_code_mappings)
