# src/yooink/data/data_manager.py

import xarray as xr
from typing import List


class DataManager:
    def __init__(self) -> None:
        """Initializes the DataManager."""
        pass

    def filter_datasets(self, datasets: List[str], exclude: str = "VELPT") -> List[str]:
        """
        Filters the dataset URLs to exclude certain instruments (e.g., 'VELPT').

        Args:
            datasets (List[str]): A list of dataset URLs.
            exclude (str): A string to exclude from the dataset URLs.

        Returns:
            List[str]: A filtered list of dataset URLs.
        """
        return [ds for ds in datasets if exclude not in ds]

    def load_dataset(self, datasets: List[str]) -> xr.Dataset:
        """
        Loads the datasets into a single xarray dataset and optimizes it.

        Args:
            datasets (List[str]): A list of URLs pointing to netCDF files.

        Returns:
            xarray.Dataset: The combined and optimized dataset.
        """
        ds = xr.open_mfdataset(datasets, combine='by_coords')
        ds = ds.swap_dims({'obs': 'time'})
        ds = ds.chunk({'time': 100})
        ds = ds.sortby('time')
        return ds
