# src/yooink/data/data_manager.py

import xarray as xr
from typing import List
import re
import requests
import warnings
import io
import numpy as np


class DataManager:
    def __init__(self) -> None:
        """Initializes the DataManager."""
        pass

    @staticmethod
    def process_file(catalog_file: str, use_dask: bool = False
                     ) -> xr.Dataset | None:
        """
        Download and process a NetCDF file into an xarray dataset.

        Args:
            catalog_file: URL or path to the NetCDF file.
            use_dask: Whether to use dask for processing (for large files).

        Returns:
            The xarray dataset.
        """
        try:
            # Convert the catalog file URL to the data URL
            tds_url = ('https://opendap.oceanobservatories.org/thredds/'
                       'fileServer/')
            data_url = re.sub(
                r'catalog.html\?dataset=', tds_url, catalog_file)

            # Download the dataset
            r = requests.get(data_url, timeout=(3.05, 120))
            if not r.ok:
                warnings.warn(f"Failed to download {catalog_file}")
                return None

            # Load the data into an xarray dataset
            data = io.BytesIO(r.content)
            if use_dask:
                ds = xr.open_dataset(
                    data, decode_cf=False, chunks='auto', mask_and_scale=False)
            else:
                ds = xr.load_dataset(
                    data, decode_cf=False, mask_and_scale=False)

            # Process the dataset
            ds = ds.swap_dims({'obs': 'time'}).reset_coords()
            ds = ds.sortby('time')

            # Drop unnecessary variables, clean time units
            keys_to_drop = ['obs', 'id', 'provenance', 'driver_timestamp',
                            'ingestion_timestamp']
            ds = ds.drop_vars([key for key in keys_to_drop
                               if key in ds.variables])

            return ds
        except Exception as e:
            warnings.warn(f"Error processing {catalog_file}: {e}")
            return None

    def merge_frames(self, frames: List[xr.Dataset]) -> xr.Dataset:
        """
        Merge multiple datasets into a single xarray dataset.

        Args:
            frames: A list of xarray datasets to merge.

        Returns:
            The merged xarray dataset.
        """
        if len(frames) == 1:
            return frames[0]

        # Attempt to merge the datasets
        try:
            data = xr.concat(frames, dim='time')
        except ValueError:
            # If concatenation fails, attempt merging one by one
            data, failed = self._frame_merger(frames[0], frames)
            if failed > 0:
                warnings.warn(f"{failed} frames failed to merge.")

        # Sort by time and remove duplicates
        data = data.sortby('time')
        _, index = np.unique(data['time'], return_index=True)
        data = data.isel(time=index)

        return data

    @staticmethod
    def _frame_merger(
            data: xr.Dataset, frames: List[xr.Dataset]
    ) -> (xr.Dataset, int):
        """
        Helper function to merge datasets one-by-one if bulk concatenation
        fails.

        Args:
            data: The initial dataset to merge.
            frames: The remaining datasets to merge into the initial one.

        Returns:
            The merged dataset and a count of failed merges.
        """
        failed = 0
        for frame in frames[1:]:
            try:
                data = xr.concat([data, frame], dim='time')
            except (ValueError, NotImplementedError):
                try:
                    data = data.merge(frame, compat='override')
                except (ValueError, NotImplementedError):
                    failed += 1
        return data, failed
