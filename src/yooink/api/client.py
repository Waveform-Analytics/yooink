# src/yooink/api/client.py

import requests
from typing import Dict, Any, Optional


class APIClient:
    def __init__(self, base_url: str, username: str, token: str) -> None:
        """
        Initializes the APIClient with base URL, API username, and token for
        authentication.

        Args:
            base_url: The base URL for the API.
            username: The API username.
            token: The API authentication token.
        """
        self.base_url = base_url
        self.auth = (username, token)
        self.session = requests.Session()

    @staticmethod
    def get_headers() -> Dict[str, str]:
        """
        Returns headers for the API request.

        Returns:
            Dict: A dictionary containing headers.
        """
        return {'Content-Type': 'application/json'}

    def make_request(
            self,
            endpoint: str,
            params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Sends a GET request to the API, with optional parameters.

        Args:
            endpoint: The API endpoint to request.
            params: Optional query parameters for the request.

        Returns:
            Any: The parsed JSON response.
        """
        url = self.construct_url(endpoint)
        response = self.session.get(
            url, auth=self.auth, headers=self.get_headers(), params=params)
        response.raise_for_status()
        return response.json()

    def construct_url(self, endpoint: str) -> str:
        """
        Constructs the full URL for the API request.

        Args:
            endpoint: The endpoint to append to the base URL.

        Returns:
            The full URL.
        """
        return f"{self.base_url}{endpoint}"

    def fetch_thredds_page(self, thredds_url: str) -> str:
        """
        Sends a GET request to the THREDDS server.

        Args:
            thredds_url: The full URL to the THREDDS server.

        Returns:
            The HTML content of the page.
        """
        response = self.session.get(thredds_url)
        response.raise_for_status()  # Raise an exception if the request failed
        return response.text
