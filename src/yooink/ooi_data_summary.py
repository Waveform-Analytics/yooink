import pandas as pd
import importlib.resources as pkg_resources

# # Load the CSV into a pandas DataFrame
with pkg_resources.open_text("yooink.data", "data_combinations.csv") as csv_file:
    ooi_data_summary = pd.read_csv(csv_file)

# Load the parquet file into a pandas Dataframe
with pkg_resources.open_binary("yooink.data", "ooi_data.parquet") as parquet_file:
    ooi_data_full = pd.read_parquet(parquet_file)
