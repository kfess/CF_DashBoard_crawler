import requests
import json


def main():
    problem_response = requests.get("https://codeforces.com/api/problemset.problems")
    problem_data = problem_response.json()

    with open("api_problems.json", "w") as f:
        json.dump(problem_data, f, indent=2)


if __name__ == "__main__":
    main()
