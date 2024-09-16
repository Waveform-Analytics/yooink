# src/yooink/request/request_manager.py

from __future__ import annotations

from typing import Any, Dict, List
from yooink.api.client import APIClient

import re
import os
import json
import time
import tempfile


class RequestManager:
    CACHE_FILE = "url_cache.json"

    def __init__(
            self,
            api_client: 'APIClient',
            use_file_cache: bool = False,
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
        return self.api_client.make_request(endpoint)

    def list_nodes(self, site: str) -> List[Dict[str, Any]]:
        """
        Lists nodes for a specific site.

        Args:
            site: The site identifier.

        Returns:
            List: A list of nodes as dictionaries.
        """
        endpoint = f"{site}/"
        return self.api_client.make_request(endpoint)

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
        return self.api_client.make_request(endpoint)

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
        return self.api_client.make_request(endpoint)

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
        return self.api_client.make_request(endpoint)

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
        return self.api_client.make_request(endpoint)

    def fetch_data_urls(
            self, site: str, node: str, sensor: str, method: str,
            stream: str, begin_datetime: str, end_datetime: str) -> List[str]:
        """
        Fetch the URLs for netCDF files from the THREDDS server based on site,
        node, data, and method. Caches the THREDDS URL to avoid repeating the
        same request.
        """

        # Create a cache key by joining the tuple elements into a string
        cache_key = (f"{site}_{node}_{sensor}_{method}_"
                     f"{stream}_{begin_datetime}_{end_datetime}")

        # Check if this request has already been cached
        if cache_key in self.cached_urls:
            print("Using cached URL for this request.")
            url_thredds = self.cached_urls[cache_key]['url']
        else:
            # Construct the initial request URL and parameters
            details = f"{site}/{node}/{sensor}/{method}/{stream}"
            params = {
                'beginDT': begin_datetime, 'endDT': end_datetime,
                'format': 'application/netcdf', 'include_provenance': 'true',
                'include_annotations': 'true'}

            # Make the request to get the dataset URLs
            response = self.api_client.make_request(details, params)

            # Extract the first URL from 'allURLs'
            url_thredds = response['allURLs'][0]

            # Cache the URL in memory and save to file if enabled
            self.cached_urls[cache_key] = {'url': url_thredds,
                                           'timestamp': time.time()}
            if self.use_file_cache:
                self.save_cache_to_file()

        # Fetch the HTML page from the THREDDS server via APIClient
        datasets_page = self.api_client.fetch_thredds_page(url_thredds)

        # Extract the .nc file URLs
        file_matches = re.findall(r'(ooi/.*?.nc)', datasets_page)
        tds_url = 'https://opendap.oceanobservatories.org/thredds/dodsC'
        datasets = [os.path.join(tds_url, match) for match in file_matches if
                    match.endswith('.nc')]

        # Only keep nc files that end in a numerical identifier
        filtered_files = [
            f for f in datasets
            if f.endswith('.nc') and f[:-3][-4:].isdigit()
        ]

        return filtered_files
