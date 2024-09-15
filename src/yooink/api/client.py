# src/yooink/api/client.py

import requests
from typing import Dict, Any


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

    def make_request(self, endpoint: str) -> Any:
        """
        Sends a GET request to the API.

        Args:
            endpoint: The API endpoint to request.

        Returns:
            Any: The parsed JSON response.
        """
        url = self.construct_url(endpoint)
        response = self.session.get(
            url, auth=self.auth, headers=self.get_headers())
        response.raise_for_status()  # Raise an exception if the request failed
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
