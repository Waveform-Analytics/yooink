# src/yooink/data/data_manager.py

import xarray as xr
import numpy as np
from typing import List, Tuple
import warnings
import io
import requests
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from functools import partial


class DataManager:
    def __init__(self) -> None:
        """Initializes the DataManager."""
        pass

    @staticmethod
    def process_files(datasets: List[str], use_dask: bool) -> List[xr.Dataset]:
        """
        Process multiple dataset files, potentially in parallel.

        Args:
            datasets: A list of dataset URLs.
            use_dask: Whether to use dask for processing.

        Returns:
            A list of processed xarray Datasets.
        """
        if len(datasets) > 5:
            part_files = partial(DataManager.process_file, use_dask=use_dask)
            with ProcessPoolExecutor(max_workers=4) as executor:
                frames = list(tqdm(executor.map(part_files, datasets),
                                   total=len(datasets),
                                   desc='Processing files'))
        else:
            frames = [DataManager.process_file(f, use_dask=use_dask) for f in
                      tqdm(datasets, desc='Processing files')]
        return frames

    @staticmethod
    def process_file(
            data_url: str,
            use_dask: bool = False
    ) -> xr.Dataset | None:
        """
        Process a single dataset file.

        Args:
            data_url: URL of the dataset file.
            use_dask: Whether to use dask for processing.

        Returns:
            Processed xarray Dataset or None if processing failed.
        """
        try:
            r = requests.get(data_url, timeout=(3.05, 120))
            if not r.ok:
                warnings.warn(f"Failed to download {data_url}")
                return None

            data = io.BytesIO(r.content)
            if use_dask:
                ds = xr.open_dataset(data, decode_cf=False, chunks='auto',
                                     mask_and_scale=False)
            else:
                ds = xr.load_dataset(data, decode_cf=False,
                                     mask_and_scale=False)

            ds = ds.swap_dims({'obs': 'time'}).reset_coords()
            ds = ds.sortby('time')

            keys_to_drop = ['obs', 'id', 'provenance', 'driver_timestamp',
                            'ingestion_timestamp']
            ds = ds.drop_vars(
                [key for key in keys_to_drop if key in ds.variables])

            return ds

        except Exception as e:
            warnings.warn(f"Error processing {data_url}: {e}")
            return None

    @staticmethod
    def merge_datasets(frames: List[xr.Dataset]) -> xr.Dataset:
        """
        Merge multiple datasets into a single dataset.

        Args:
            frames: List of xarray Datasets to merge.

        Returns:
            Merged xarray Dataset.
        """
        if len(frames) == 1:
            return frames[0]

        try:
            data = xr.concat(frames, dim='time')
        except ValueError:
            data, failed = DataManager._frame_merger(frames[0], frames)
            if failed > 0:
                warnings.warn(f"{failed} frames failed to merge.")

        data = data.sortby('time')
        _, index = np.unique(data['time'], return_index=True)
        data = data.isel(time=index)

        return data

    @staticmethod
    def _frame_merger(
            data: xr.Dataset,
            frames: List[xr.Dataset]
    ) -> Tuple[xr.Dataset, int]:
        """
        Helper method to merge datasets one by one.

        Args:
            data: Initial dataset to merge with.
            frames: List of datasets to merge.

        Returns:
            Tuple of merged dataset and count of failed merges.
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

    @staticmethod
    def optimize_dataset(ds: xr.Dataset) -> xr.Dataset:
        """
        Optimize the dataset for better performance.

        Args:
            ds: xarray Dataset to optimize.

        Returns:
            Optimized xarray Dataset.
        """
        ds = ds.chunk({'time': 100})
        return ds
