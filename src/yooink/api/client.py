# src/yooink/api/client.py

import requests
from typing import Dict, Any, Optional
from enum import Enum


class M2MInterface(Enum):
    ANNO_URL = '12580/anno/'  # Annotation Information
    ASSET_URL = '12587/asset/'  # Asset and Calibration Information
    DEPLOY_URL = '12587/events/deployment/inv/'  # Deployment Information
    SENSOR_URL = '12576/sensor/inv/'  # Sensor Information
    VOCAB_URL = '12586/vocab/inv/'  # Vocabulary Information
    STREAM_URL = '12575/stream/byname/'  # Stream Information
    PARAMETER_URL = '12575/parameter/'  # Parameter Information


class APIClient:
    # Set Up Constants:
    # Base URL for accessing OOI data
    BASE_URL = 'https://ooinet.oceanobservatories.org/api/m2m/'
    # different M2M interfaces to the base URL
    ANNO_URL = '12580/anno/'  # Annotation Information
    ASSET_URL = '12587/asset/'  # Asset and Calibration Information
    DEPLOY_URL = '12587/events/deployment/inv/'  # Deployment Information
    SENSOR_URL = '12576/sensor/inv/'  # Sensor Information
    VOCAB_URL = '12586/vocab/inv/'  # Vocabulary Information
    STREAM_URL = '12575/stream/byname/'  # Stream Information
    PARAMETER_URL = '12575/parameter/'  # Parameter Information

    def __init__(self, username: str, token: str) -> None:
        """
        Initializes the APIClient with base URL, API username, and token for
        authentication.

        Args:
=           username: The API username.
            token: The API authentication token.
        """
        self.auth = (username, token)
        self.session = requests.Session()

    @staticmethod
    def get_headers() -> Dict[str, str]:
        """
        Returns headers for the API request.

        Returns:
            A dictionary containing headers.
        """
        return {'Content-Type': 'application/json'}

    def make_request(
            self,
            interface: M2MInterface,
            endpoint: str,
            params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Sends a GET request to the API, with optional parameters.

        Args:
            interface: The M2M interface to use (from M2MInterface Enum).
            endpoint: The API endpoint to request.
            params: Optional query parameters for the request.

        Returns:
            The parsed JSON response.
        """
        url = self.construct_url(interface, endpoint)
        response = self.session.get(
            url, auth=self.auth, headers=self.get_headers(), params=params)
        response.raise_for_status()
        return response.json()

    def construct_url(self, interface: M2MInterface, endpoint: str) -> str:
        """
        Constructs the full URL for the API request based on the interface and endpoint.

        Args:
            interface: The M2M interface to use (from M2MInterface Enum).
            endpoint: The specific endpoint to append to the interface.

        Returns:
            The full URL.
        """
        return f"{self.BASE_URL}{interface.value}{endpoint}"

    def fetch_thredds_page(self, thredds_url: str) -> str:
        """
        Sends a GET request to the THREDDS server. Uses the session's
        built-in retry mechanism for handling delays in data availability.

        Args:
            thredds_url: The full URL to the THREDDS server.

        Returns:
            The HTML content of the page.

        Raises:
            Exception: If the data is still unavailable after all retries.
        """
        response = self.session.get(thredds_url)
        response.raise_for_status()
        return response.text
