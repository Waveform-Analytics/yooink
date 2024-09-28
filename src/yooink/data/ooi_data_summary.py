import pandas as pd
import importlib.resources as pkg_resources


class OOIDataSummary:
    def __init__(self, csv_filename: str):
        self.csv_filename = csv_filename
        self.dataframe = None

    def load_data(self):
        """Load the CSV into a pandas DataFrame."""
        with pkg_resources.open_text('yooink.data', self.csv_filename) as csv_file:
            self.dataframe = pd.read_csv(csv_file)
        return self.dataframe
