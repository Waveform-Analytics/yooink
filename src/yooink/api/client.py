# src/yooink/api/client.py

import time
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
            A dictionary containing headers.
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
            The parsed JSON response.
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

    def fetch_thredds_page(
            self,
            thredds_url: str,
            retries: int = 5,
            backoff_factor: float = 2.0
    ) -> str:
        """
        Sends a GET request to the THREDDS server, with retry mechanism for
        handling delays in data availability.

        Args:
            thredds_url: The full URL to the THREDDS server.
            retries: The number of retry attempts if the data is not ready.
            backoff_factor: Multiplier for delay between retries.

        Returns:
            The HTML content of the page.

        Raises:
            Exception: If the data is still unavailable after the retry limit.
        """
        attempt = 0
        while attempt < retries:
            try:
                response = self.session.get(thredds_url)
                response.raise_for_status()
                return response.text
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    attempt += 1
                    delay = backoff_factor ** attempt
                    print(f"Thredds data not ready yet, retrying in {delay} "
                          f"seconds...")
                    time.sleep(delay)
                else:
                    raise
        else:
            raise Exception(f"Data still not available after {retries} "
                            f"retries.")
