import requests
import json


def main():
    """
    Main function to fetch contest set from Codeforces API and save it to a file.

    Raises
    ------
    Exception
        If the request fails or if the response status code is not 200.
    """
    url = "https://codeforces.com/api/contest.list"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to access {url}") from e

    try:
        problem_data = response.json()
    except ValueError as e:
        raise Exception(f"Failed to decode response from {url}") from e

    if problem_data["status"] != "OK":
        raise Exception(f"Unexpected response from {url}")

    with open("./data/contest-list.json", "w") as f:
        json.dump(problem_data, f, indent=2)


if __name__ == "__main__":
    main()
