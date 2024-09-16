# src/yooink/request/request_manager.py

from __future__ import annotations

from typing import Any, Dict, List
from yooink.api.client import APIClient

import re
import os


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
            self,
            site: str,
            node: str,
            sensor: str,
            method: str,
            stream: str,
            begin_datetime: str,
            end_datetime: str
    ) -> List[str]:
        """
        Fetch the URLs for netCDF files from the THREDDS server based on site,
        node, data, and method.

        Args:
            site: The site identifier.
            node: The node identifier.
            sensor: The data identifier.
            method: The method (e.g., 'telemetered').
            stream: The data stream.
            begin_datetime: The start date/time for the data (ISO format).
            end_datetime: The end date/time for the data (ISO format).

        Returns:
            A list of URLs pointing to netCDF files.
        """
        details = f"{site}/{node}/{sensor}/{method}/{stream}"
        params = {
            'beginDT': begin_datetime,
            'endDT': end_datetime,
            'format': 'application/netcdf',
            'include_provenance': 'true',
            'include_annotations': 'true'
        }

        response = self.api_client.make_request(details, params)

        url_thredds = response['allURLs'][0]

        datasets_page = self.api_client.fetch_thredds_page(url_thredds)

        file_matches = re.findall(r'(ooi/.*?.nc)', datasets_page)
        tds_url = 'https://opendap.oceanobservatories.org/thredds/dodsC'
        datasets = [os.path.join(tds_url, match) for match in file_matches
                    if match.endswith('.nc')]

        return datasets
