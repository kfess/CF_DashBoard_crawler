import requests
import json


def main():
    contest_response = requests.get("https://codeforces.com/api/contest.list")
    contest_data = contest_response.json()

    with open("contest-list.json", "w") as f:
        json.dump(contest_data, f, indent=2)

    problem_response = requests.get("https://codeforces.com/api/problemset.problems")
    problem_data = problem_response.json()

    with open("problems.json", "w") as f:
        json.dump(problem_data, f, indent=2)


if __name__ == "__main__":
    main()
