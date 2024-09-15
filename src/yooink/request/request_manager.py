# src/yooink/request/request_manager.py

from __future__ import annotations

from typing import Any, Dict, List
from yooink.api.client import APIClient

import re
import os
import requests


class RequestManager:
    def __init__(self, api_client: APIClient) -> None:
        """
        Initializes the RequestManager with an instance of APIClient.

        Args:
            api_client: An instance of the APIClient class.
        """
        self.api_client = api_client

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
        Lists methods available for a specific sensor.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The sensor identifier.

        Returns:
            A list of methods as dictionaries.
        """
        endpoint = f"{site}/{node}/{sensor}/"
        return self.api_client.make_request(endpoint)

    def get_metadata(
            self, site: str, node: str, sensor: str) -> Dict[str, Any]:
        """
        Retrieves metadata for a specific sensor.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The sensor identifier.

        Returns:
            The metadata as a dictionary.
        """
        endpoint = f"{site}/{node}/{sensor}/metadata"
        return self.api_client.make_request(endpoint)

    def list_streams(
            self, site: str, node: str, sensor: str, method: str) \
            -> List[Dict[str, Any]]:
        """
        Lists available streams for a specific sensor and method.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The sensor identifier.
            method: The method (e.g., telemetered).

        Returns:
            A list of streams as dictionaries.
        """
        endpoint = f"{site}/{node}/{sensor}/{method}/"
        return self.api_client.make_request(endpoint)

    def fetch_data_urls(self, site: str, node: str, sensor: str, method: str,
                        begin_datetime: str, end_datetime: str) -> List[str]:
        """
        Fetch the URLs for netCDF files from the THREDDS server based on site,
        node, sensor, and method.

        Args:
            site (str): The site identifier.
            node (str): The node identifier.
            sensor (str): The sensor identifier.
            method (str): The method (e.g., 'telemetered').
            begin_datetime (str): The start date/time for the data (ISO format)
            end_datetime (str): The end date/time for the data (ISO format)

        Returns:
            List[str]: A list of URLs pointing to netCDF files.
        """
        # Construct the initial request URL and parameters
        details = f"{site}/{node}/{sensor}/{method}"
        params = {'beginDT': begin_datetime, 'endDT': end_datetime,
            'format': 'application/netcdf', 'include_provenance': 'true',
            'include_annotations': 'true'}

        # Make the request to get the dataset URLs
        response = self.api_client.make_request(details, params)

        # Extract the first URL from 'allURLs'
        url_thredds = response['allURLs'][0]

        # Retrieve the available datasets from the THREDDS server
        datasets_page = requests.get(url_thredds).text

        # Extract the .nc file URLs
        file_matches = re.findall(r'(ooi/.*?.nc)', datasets_page)
        tds_url = 'https://opendap.oceanobservatories.org/thredds/dodsC'
        datasets = [os.path.join(tds_url, match) for match in file_matches if
                    match.endswith('.nc')]

        return datasets
