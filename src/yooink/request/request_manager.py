# src/yooink/request/request_manager.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from yooink.api.client import APIClient, M2MInterface
from yooink.data.data_manager import DataManager

import re
import json
import time
from tqdm import tqdm
import os
import xarray as xr
import requests
import sys


class RequestManager:
    """
    Class responsible for managing requests

    This class communicates with both the API client and the data manager
    classes.

    """
    CACHE_FILE = "url_cache.json"

    def __init__(
            self,
            api_client: APIClient,
            data_manager: DataManager,
    ) -> None:
        """
        Initializes the RequestManager with an instance of APIClient,
        DataManager, and cache options.

        Args:
            api_client: An instance of the APIClient class.
            data_manager: An instance of the DataManager class.
            use_file_cache: Whether to enable file-based caching (default
                False).
            cache_expiry: The number of days before cache entries expire
                (default 14 days).
        """
        self.api_client = api_client
        self.data_manager = data_manager

    def list_sites(self) -> List[Dict[str, Any]]:
        """
        Lists all available sites from the API.

        Returns:
            A list of sites as dictionaries.
        """
        endpoint = ""
        return self.api_client.make_request(M2MInterface.SENSOR_URL, endpoint)

    def list_nodes(self, site: str) -> List[Dict[str, Any]]:
        """
        Lists nodes for a specific site.

        Args:
            site: The site identifier.

        Returns:
            List: A list of nodes as dictionaries.
        """
        endpoint = f"{site}/"
        return self.api_client.make_request(M2MInterface.SENSOR_URL, endpoint)

    def list_sensors(self, site: str, node: str) -> List[Dict[str, Any]]:
        """
        Lists sensors for a specific site and node.

        Args:
            site: The site identifier.
            node: The node identifier.

        Returns:
            List: A list of sensors as dictionaries.
        """
        endpoint = f"{site}/{node}/"
        return self.api_client.make_request(M2MInterface.SENSOR_URL, endpoint)

    def list_methods(
            self, site: str, node: str, sensor: str) -> List[Dict[str, Any]]:
        """
        Lists methods available for a specific data.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The data identifier.

        Returns:
            A list of methods as dictionaries.
        """
        endpoint = f"{site}/{node}/{sensor}/"
        return self.api_client.make_request(M2MInterface.SENSOR_URL, endpoint)

    def get_metadata(
            self, site: str, node: str, sensor: str) -> Dict[str, Any]:
        """
        Retrieves metadata for a specific data.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The data identifier.

        Returns:
            The metadata as a dictionary.
        """
        endpoint = f"{site}/{node}/{sensor}/metadata"
        return self.api_client.make_request(M2MInterface.SENSOR_URL, endpoint)

    def list_streams(
            self, site: str, node: str, sensor: str, method: str) \
            -> List[Dict[str, Any]]:
        """
        Lists available streams for a specific data and method.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The data identifier.
            method: The method (e.g., telemetered).

        Returns:
            A list of streams as dictionaries.
        """
        endpoint = f"{site}/{node}/{sensor}/{method}/"
        return self.api_client.make_request(M2MInterface.SENSOR_URL, endpoint)

    def list_deployments(
            self, site: str, node: str, sensor: str
    ) -> List[Dict[str, Any]]:
        """
        Lists deployments for a specific site, node, and sensor.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The sensor identifier.

        Returns:
            A list of deployments as dictionaries.
        """
        endpoint = f"{site}/{node}/{sensor}"
        return self.api_client.make_request(M2MInterface.DEPLOY_URL, endpoint)

    def get_sensor_information(
            self, site: str, node: str, sensor: str, deploy: str | int
    ) -> list:
        """
        Retrieves sensor metadata for a specific deployment.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The sensor identifier.
            deploy: The deployment number.

        Returns:
            The sensor information as a dictionary.
        """
        endpoint = f"{site}/{node}/{sensor}/{str(deploy)}"
        return self.api_client.make_request(M2MInterface.DEPLOY_URL, endpoint)

    def get_deployment_dates(
            self,
            site: str,
            node: str,
            sensor: str,
            deploy: str | int
    ) -> Optional[Dict[str, str]]:
        """
        Retrieves the start and stop dates for a specific deployment.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The sensor identifier.
            deploy: The deployment number.

        Returns:
            A dictionary with the start and stop dates, or None if the
                information is not available.
        """
        sensor_info = self.get_sensor_information(site, node, sensor,
                                                  str(deploy))

        if sensor_info:
            start = time.strftime(
                '%Y-%m-%dT%H:%M:%S.000Z',
                time.gmtime(sensor_info[0]['eventStartTime'] / 1000.0))

            if sensor_info[0].get('eventStopTime'):
                stop = time.strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z',
                    time.gmtime(sensor_info[0]['eventStopTime'] / 1000.0))
            else:
                stop = time.strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z',
                    time.gmtime(time.time()))

            return {'start': start, 'stop': stop}
        else:
            return None

    def get_sensor_history(self, uid: str) -> Dict[str, Any]:
        """
        Retrieves the asset and calibration information for a sensor across all
        deployments.

        Args:
            uid: The unique asset identifier (UID).

        Returns:
            The sensor history as a dictionary.
        """
        endpoint = f"asset/deployments/{uid}?editphase=ALL"
        return self.api_client.make_request(M2MInterface.DEPLOY_URL, endpoint)

    def fetch_data(
            self,
            site: str,
            node: str,
            sensor: str,
            method: str,
            stream: str,
            begin_datetime: str,
            end_datetime: str,
            use_dask: bool = False
    ) -> xr.Dataset | None:
        """
        Fetch the data from the THREDDS server based on instrument attributes.

        Args:
            site: Site identifier.
            node: Node identifier.
            sensor: Sensor identifier.
            method: Delivery method (e.g., 'telemetered').
            stream: Stream name.
            begin_datetime: Start time for data request.
            end_datetime: End time for data request.
            use_dask: Boolean flag indicating whether to load data using dask
                arrays.

        Returns:
            An xarray.Dataset containing the compiled data from the THREDDS
            server, or None.
        """
        print(f"Requesting data for site: {site}, node: {node}, "
              f"sensor: {sensor}, method: {method}, stream: {stream}")
        data = self.wait_for_m2m_data(site, node, sensor, method, stream,
                                      begin_datetime, end_datetime)
        if not data:
            print("Request failed or timed out. Please try again later.")
            return None

        datasets = self.get_filtered_files(data)

        frames = self.data_manager.process_files(datasets, use_dask)
        merged_data = self.data_manager.merge_datasets(frames)
        optimized_data = self.data_manager.optimize_dataset(merged_data)

        return optimized_data

    def wait_for_m2m_data(
            self,
            site: str,
            node: str,
            sensor: str,
            method: str,
            stream: str,
            begin_datetime: str,
            end_datetime: str
    ) -> Any | None:
        """
        Request data from the M2M API and wait for completion, displaying
        progress with tqdm.
        """
        # Set up request details
        params = {
            'beginDT': begin_datetime, 'endDT': end_datetime,
            'format': 'application/netcdf', 'include_provenance': 'true',
            'include_annotations': 'true'}
        details = f"{site}/{node}/{sensor}/{method}/{stream}"

        # Make the request
        response = self.api_client.make_request(
            M2MInterface.SENSOR_URL,
            details, params)

        if 'allURLs' not in response:
            print("No URLs found in the response.")
            return None

        # Get the async URL and status URL
        url = [url for url in response['allURLs'] if
               re.match(r'.*async_results.*', url)][0]
        check_complete = url + '/status.txt'

        # Use tqdm to wait for completion
        print("Waiting for OOINet to process and prepare the data. This may "
              "take up to 20 minutes.")
        with tqdm(total=400, desc='Waiting') as bar:
            for _ in range(400):
                try:
                    r = self.api_client.session.get(check_complete, timeout=10)
                    if r.status_code == 200:
                        return response
                    elif r.status_code == 404:
                        # If it's a 404, the request might not be ready yet
                        pass
                    else:
                        r.raise_for_status()
                except requests.exceptions.Timeout:
                    print("Request timed out. Retrying...")
                except requests.exceptions.RequestException as e:
                    print(f"Error checking status: {e}")

                bar.update()
                time.sleep(3)

        print("Data request timed out. Please try again later.")
        return None

    def get_filtered_files(
            self,
            data: dict,
            tag: str = r'.*\.nc$'
    ) -> List[str]:
        """
        Extract the relevant file URLs from the M2M response, filtered using a
        regex tag.

        Args:
            data: JSON response from the M2M API request.
            tag: A regex tag to filter the .nc files (default is to match any
                .nc file).

        Returns:
            A list of filtered .nc file URLs.
        """
        # Fetch the datasets page from the THREDDS server
        datasets_page = self.api_client.fetch_thredds_page(data['allURLs'][0])

        # Use the list_files function with regex to filter the files
        return self.list_files(datasets_page, tag=tag)

    @staticmethod
    def list_files(
            page_content: str,
            tag: str = r'.*\.nc$'
    ) -> List[str]:
        """
        Create a list of the NetCDF data files in the THREDDS catalog using
        regex.

        Args:
            page_content: HTML content of the THREDDS catalog page.
            tag: A regex pattern to filter files.

        Returns:
            A list of files that match the regex tag.
        """
        pattern = re.compile(tag)
        soup = BeautifulSoup(page_content, 'html.parser')
        return [node.get('href') for node in
                soup.find_all('a', string=pattern)]
