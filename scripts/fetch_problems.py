import requests
import json
from typing import Any, Dict

# Constants
API_URL = "https://codeforces.com/api/problemset.problems"
OUTPUT_FILE_PATH = "./data/api_problems.json"

# Custom Exceptions
class FetchError(Exception):
    """Custom error for fetching data from the API."""

class DecodeError(Exception):
    """Custom error for decoding the response."""

class APIResponseError(Exception):
    """Custom error for unexpected API response."""


def main():
    """
    Main function to fetch problem set from Codeforces API and save it to a file.

    Raises
    ------
    Exception
        If the request fails or if the response status code is not 200.
    """
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise FetchError(f"Failed to access {API_URL}") from e

    try:
        problem_data = response.json()
    except ValueError as e:
        raise DecodeError(f"Failed to decode response from {API_URL}") from e

    if problem_data["status"] != "OK":
        raise APIResponseError(f"Unexpected response from {API_URL}")

    with open(OUTPUT_FILE_PATH, "w") as f:
        json.dump(problem_data, f, indent=2)


if __name__ == "__main__":
    main()
