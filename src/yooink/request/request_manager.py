# src/yooink/request/request_manager.py

from __future__ import annotations

from typing import Any, Dict, List
from yooink.api.client import APIClient


class RequestManager:
    def __init__(self, api_client: APIClient) -> None:
        """
        Initializes the RequestManager with an instance of APIClient.

        Args:
            api_client (APIClient): An instance of the APIClient class.
        """
        self.api_client = api_client

    def list_sites(self) -> List[Dict[str, Any]]:
        """
        Lists all available sites from the API.

        Returns:
            List[Dict[str, Any]]: A list of sites as dictionaries.
        """
        endpoint = ""
        return self.api_client.make_request(endpoint)

    def list_nodes(self, site: str) -> List[Dict[str, Any]]:
        """
        Lists nodes for a specific site.

        Args:
            site (str): The site identifier.

        Returns:
            List[Dict[str, Any]]: A list of nodes as dictionaries.
        """
        endpoint = f"{site}/"
        return self.api_client.make_request(endpoint)

    def list_sensors(self, site: str, node: str) -> List[Dict[str, Any]]:
        """
        Lists sensors for a specific site and node.

        Args:
            site (str): The site identifier.
            node (str): The node identifier.

        Returns:
            List[Dict[str, Any]]: A list of sensors as dictionaries.
        """
        endpoint = f"{site}/{node}/"
        return self.api_client.make_request(endpoint)

    def list_methods(
            self, site: str, node: str, sensor: str) -> List[Dict[str, Any]]:
        """
        Lists methods available for a specific sensor.

        Args:
            site (str): The site identifier.
            node (str): The node identifier.
            sensor (str): The sensor identifier.

        Returns:
            List[Dict[str, Any]]: A list of methods as dictionaries.
        """
        endpoint = f"{site}/{node}/{sensor}/"
        return self.api_client.make_request(endpoint)

    def get_metadata(
            self, site: str, node: str, sensor: str) -> Dict[str, Any]:
        """
        Retrieves metadata for a specific sensor.

        Args:
            site (str): The site identifier.
            node (str): The node identifier.
            sensor (str): The sensor identifier.

        Returns:
            Dict[str, Any]: The metadata as a dictionary.
        """
        endpoint = f"{site}/{node}/{sensor}/metadata"
        return self.api_client.make_request(endpoint)

    def list_streams(
            self, site: str, node: str, sensor: str, method: str) \
            -> List[Dict[str, Any]]:
        """
        Lists available streams for a specific sensor and method.

        Args:
            site (str): The site identifier.
            node (str): The node identifier.
            sensor (str): The sensor identifier.
            method (str): The method (e.g., telemetered).

        Returns:
            List[Dict[str, Any]]: A list of streams as dictionaries.
        """
        endpoint = f"{site}/{node}/{sensor}/{method}/"
        return self.api_client.make_request(endpoint)
