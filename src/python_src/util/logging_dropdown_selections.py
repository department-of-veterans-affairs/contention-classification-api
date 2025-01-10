import csv


def build_logging_table(filepath: str) -> list[str]:
    """
    Builds list of dropdown options to use for logging from the most current
    dropdown conditions lookup table csv.

    Parameters:
    -----------
    filepath: str
        The filepath to the current version of the autosuggestion list

    Returns
    -------
    list[str]
        List of autosuggestion names for use in logging
    """
    dropdown_values = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dropdown_values.append(row["Autosuggestion Name"].strip().lower())
    return dropdown_values
