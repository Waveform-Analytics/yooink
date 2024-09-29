# src/yooink/request/request_manager.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from bs4 import BeautifulSoup
from xarray import Dataset

from yooink import APIClient, M2MInterface, DataManager

import re
import json
import time
import tempfile
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import os
import requests
import sys
from functools import partial


class RequestManager:
    CACHE_FILE = "url_cache.json"

    def __init__(
            self,
            api_client: APIClient,
            use_file_cache: bool = True,
            cache_expiry: int = 14
    ) -> None:
        """
        Initializes the RequestManager with an instance of APIClient and cache
        options.

        Args:
            api_client: An instance of the APIClient class.
            use_file_cache: Whether to enable file-based caching (default
                False).
            cache_expiry: The number of days before cache entries expire
                (default 14 days).
        """
        self.api_client = api_client
        self.data_manager = DataManager()
        self.cached_urls = {}
        self.use_file_cache = use_file_cache
        self.cache_expiry = cache_expiry

        # Load cache from file if enabled
        if self.use_file_cache:
            self.load_cache_from_file()

    def load_cache_from_file(self) -> None:
        """
        Loads the cached URLs from a JSON file and removes expired entries.
        If the file is empty or contains invalid JSON, it initializes an empty
        cache.
        """
        if not os.path.exists(self.CACHE_FILE):
            return

        try:
            with open(self.CACHE_FILE, 'r') as file:
                content = file.read().strip()

                if not content:  # Check if file is empty
                    print("Cache file is empty. Initializing new cache.")
                    file_cache = {}
                else:
                    file_cache = json.loads(content)

            # Filter out expired cache entries
            current_time = time.time()
            valid_cache = {
                key: value for key, value in file_cache.items() if
                current_time - value['timestamp'] < self.cache_expiry * 86400
            }

            self.cached_urls = valid_cache
            self.save_cache_to_file()  # Save the updated cache

        except json.JSONDecodeError:
            print("Cache file contains invalid JSON. Initializing new cache.")
            self.cached_urls = {}
            self.save_cache_to_file()

    def save_cache_to_file(self) -> None:
        """
        Saves the current cached URLs to a JSON file, appending new URLs to the
        existing cache.
        """
        # Load existing cache if it exists
        file_cache = {}
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as file:
                    content = file.read().strip()
                    if content:
                        file_cache = json.loads(content)
            except json.JSONDecodeError:
                print(
                    "Existing cache file contains invalid JSON. "
                    "Overwriting with new cache.")

        # Merge the in-memory cache with the file cache
        file_cache.update(self.cached_urls)

        # Write the merged cache to a temporary file, then replace the original
        # file
        temp_file = None
        try:
            temp_dir = os.path.dirname(self.CACHE_FILE)
            with tempfile.NamedTemporaryFile('w', dir=temp_dir,
                                             delete=False) as temp_file:
                json.dump(file_cache, temp_file)

            # Replace the original cache file with the temp file
            os.replace(temp_file.name, self.CACHE_FILE)

        except Exception as e:
            print(f"Error saving cache: {e}")

            # Ensure temp file is deleted if something goes wrong
            if temp_file:
                os.remove(temp_file.name)

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
            self, site: str, node: str, sensor: str, deploy: Union[int, str]
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
            self, site: str, node: str, sensor: str, method: str,
            stream: str, begin_datetime: str, end_datetime: str,
            use_dask=False, tag: str = r'.*\.nc$') -> Dataset | None:
        """
        Fetch the URLs for netCDF files from the THREDDS server based on site,
        node, data, and method.
        """
        # Construct a cache key using relevant details
        cache_key = (f"{site}_{node}_{sensor}_{method}_{stream}_"
                     f"{begin_datetime}_{end_datetime}")

        # Check if the request is already cached
        if cache_key in self.cached_urls:
            print(f"Using cached URL for request: {cache_key}")
            async_url = self.cached_urls[cache_key]['async_url']
            tds_url = self.cached_urls[cache_key]['tds_url']
            # You can now re-check the status of this request
            check_complete = async_url + '/status.txt'
            response = self.api_client.session.get(check_complete)
            if response.status_code == requests.codes.ok:
                datasets = self.get_filtered_files(
                    {'allURLs': [tds_url]}, tag)
            else:
                print(f"Data not ready yet for cached request: {cache_key}")
                return None
        else:
            # Proceed with normal request flow if not cached
            print(
                f"Requesting data for site: {site}, node: {node}, "
                f"sensor: {sensor}, method: {method}, stream: {stream}")
            data = self.wait_for_m2m_data(site, node, sensor, method, stream,
                                          begin_datetime, end_datetime)
            if not data:
                print("Request failed or timed out. Please try again later.")
                return None

            # Extract URLs from the M2M response
            datasets = self.get_filtered_files(data)

        # Continue with processing and merging the datasets as before
        if len(datasets) > 5:
            part_files = partial(self.data_manager.process_file,
                                 use_dask=use_dask)
            with ProcessPoolExecutor(max_workers=4) as executor:
                frames = list(tqdm(executor.map(part_files, datasets),
                                   total=len(datasets),
                                   desc='Processing files'))
        else:
            frames = [self.data_manager.process_file(f, use_dask=use_dask)
                      for f in
                      tqdm(datasets, desc='Processing files')]

        return self.data_manager.merge_frames(frames)

    def wait_for_m2m_data(
            self, site: str, node: str, sensor: str, method: str,
            stream: str, begin_datetime: str, end_datetime: str) -> Any | None:
        """
        Request data from the M2M API and wait for completion, displaying
        progress with tqdm.
        """
        # Step 1: Set up request details
        params = {
            'beginDT': begin_datetime, 'endDT': end_datetime,
            'format': 'application/netcdf', 'include_provenance': 'true',
            'include_annotations': 'true'}
        details = f"{site}/{node}/{sensor}/{method}/{stream}"

        # Step 2: Make the request and get the response
        response = self.api_client.make_request(M2MInterface.SENSOR_URL,
                                                details, params)

        if 'allURLs' not in response:
            print("No URLs found in the response.")
            return None

        # Step 3: Extract the async URL and status URL
        url = [url for url in response['allURLs'] if
               re.match(r'.*async_results.*', url)][0]
        thredds_url = response['allURLs'][0]
        check_complete = url + '/status.txt'

        # Step 4: Cache the URL immediately after the request is submitted
        cache_key = (f"{site}_{node}_{sensor}_{method}_{stream}_"
                     f"{begin_datetime}_{end_datetime}")
        self.cached_urls[cache_key] = {
            'tds_url': thredds_url,
            'async_url': url,
            'timestamp': time.time()
        }

        if self.use_file_cache:
            self.save_cache_to_file()  # Save cache immediately

        # Step 5: Use tqdm to wait for completion
        print(
            "Waiting for OOINet to process and prepare the data. This may "
            "take up to 20 minutes.")
        with tqdm(total=400, desc='Waiting', file=sys.stdout) as bar:
            for i in range(400):
                try:
                    r = self.api_client.session.get(check_complete,
                                                    timeout=(3.05, 120))
                    if r.status_code == 200:  # Data is ready
                        bar.n = 400  # Complete the progress bar
                        return response
                    elif r.status_code == 404:
                        pass
                except requests.exceptions.RequestException as e:
                    print(f"Error during status check: {e}")

                bar.update()
                bar.refresh()
                time.sleep(3)  # Wait 3 seconds between checks

        # If we exit the loop without the request being ready, return None
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
