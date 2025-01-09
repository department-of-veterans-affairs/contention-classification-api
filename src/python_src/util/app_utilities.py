import yaml


def load_config(config_file):
    with open(config_file, "r") as f:
        data = yaml.safe_load(f)
    return data
