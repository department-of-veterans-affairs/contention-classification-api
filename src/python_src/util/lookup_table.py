import csv


class DiagnosticCodeLookupTable:
    """
    Lookup table for mapping diagnostic codes to contention classification codes

    Attributes:
    ----------
    csv_filepath: str
        Path to the csv file containing the correct version of the lookup table
    input_key: str
        The value to use as the key for the lookup table
    classification_code: str
        The column name to load the classification code to the lookup table
    classification_name: str
        The column name to load the classification name to the lookup table
    lut_default_value: dict[str, str|int]
        The default return value for classifications with both classification name and code set to None
    """

    def __init__(
        self,
        csv_filepath: str,
        input_key: str,
        classification_code: str,
        classification_name: str,
        lut_default_value: dict[str, str | int],
    ):
        self.csv_filepath = csv_filepath
        self.input_key = input_key
        self.classification_code = classification_code
        self.classification_name = classification_name
        self.lut_default_value = lut_default_value
        self.classification_code_mappings = {}
        with open(self.csv_filepath, "r") as fh:
            csv_reader = csv.DictReader(fh)
            for row in csv_reader:
                table_key = row[str(self.input_key)].strip().lower()
                self.classification_code_mappings[table_key] = {
                    "classification_code": int(row[self.classification_code]),
                    "classification_name": row[self.classification_name],  # note underscore different from contention LUT
                }

    def get(self, input_key: int, default_value=None):
        default_value = self.lut_default_value
        classification = self.classification_code_mappings.get(str(input_key), default_value)
        return classification

    def __len__(self):
        return len(self.classification_code_mappings)


class ContentionTextLookupTable:
    """
    Maps contention text to classification code
    For mapping autosuggestion combobox values of the add disabilities page of the 526-ez form
      as well as free text entries to a classification (name and code)

    Attributes:
    ----------
    csv_filepath: str
        Path to the csv file containing the correct version of the lookup table
    input_key: str
        The value to use as the key for the lookup table
    classification_code: str
        The column name to load the classification code to the lookup table
    classification_name: str
        The column name to load the classification name to the lookup table
    lut_default_value: dict[str, str|int]
        The default return value for classifications with both classification name and code set to None
    """

    def __init__(
        self,
        csv_filepath: str,
        input_key: str,
        classification_code: str,
        classification_name: str,
        lut_default_value: dict[str, str | int],
    ):
        self.csv_filepath = csv_filepath
        self.input_key = input_key
        self.classification_code = classification_code
        self.classification_name = classification_name
        self.lut_default_value = lut_default_value
        self.classification_code_mappings = {}
        with open(self.csv_filepath, "r") as fh:
            csv_reader = csv.DictReader(fh)
            for row in csv_reader:
                table_key = row[self.input_key].strip().lower()
                self.classification_code_mappings[table_key] = {
                    "classification_code": int(row[self.classification_code]),
                    "classification_name": row[self.classification_name],
                }

    def get(self, input_str: str, default_value=None):
        default_value = self.lut_default_value
        input_str = input_str.strip().lower()
        classification = self.classification_code_mappings.get(input_str, default_value)
        return classification

    def __len__(self):
        return len(self.classification_code_mappings)
