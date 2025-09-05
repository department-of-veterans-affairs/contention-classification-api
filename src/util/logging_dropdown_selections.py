from .lookup_tables_utilities import read_csv_to_list


def build_logging_table(filepath: str, autocomplete_columns: list[str], active_autocomplete: str) -> list[str]:
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
    rows = read_csv_to_list(filepath)
    for row in rows:
        if row[active_autocomplete] == "Active":
            for col in autocomplete_columns:
                if row[col]:
                    dropdown_values.append(row[col].strip().lower())
    return dropdown_values
