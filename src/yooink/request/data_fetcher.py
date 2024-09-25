# src/yooink/request/data_fetcher.py

from yooink.api.client import APIClient
from yooink.request.request_manager import RequestManager
from yooink.data.data_manager import DataManager

import os


class DataFetcher:
    def __init__(self, username=None, token=None) -> None:
        """ Initialize the DatasetFetcher. """
        self.username = username or os.getenv('OOI_USER')
        self.token = token or os.getenv('OOI_TOKEN')
        self.api_client = APIClient(self.username, self.token)
        self.request_manager = RequestManager(self.api_client,
                                              use_file_cache=True)
        self.data_manager = DataManager()

    def get_dataset(self, site, node, sensor, method, stream,
                    begin_datetime, end_datetime):
        """Fetches the dataset for the given parameters."""
        # Fetch dataset URLs
        datasets = (
            self.request_manager.fetch_data(site, node, sensor, method, stream,
                                            begin_datetime, end_datetime)
        )

        # Load the datasets into an xarray dataset
        ds = self.data_manager.load_dataset(datasets)
        return ds
