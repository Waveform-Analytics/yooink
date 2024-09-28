import pandas as pd
import importlib.resources as pkg_resources

# Load the CSV into a pandas DataFrame as soon as the module is imported
with pkg_resources.open_text(
        'yooink.data', 'data_combinations.csv') as csv_file:
    ooi_data_summary = pd.read_csv(csv_file)
