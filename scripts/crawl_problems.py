import argparse
import json
import re
import time
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup

from merge_problems import merge_problems, merge_problem_stats

SLEEP = 1  # seconds


def make_request(url: str):
    """
    Send a GET request to the specified URL and return the response.

    Parameters
    ----------
    url : str
        The URL to which the request is sent.

    Returns
    -------
    response : requests.Response
        The response received from the server.

    Raises
    ------
    Exception
        If the request fails or if the response status code is not 200.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to access {url}") from e

    return response


def get_avail_contest_ids():
    """
    Codeforces API を利用して、アクセス可能なコンテストの ID を取得する。

    Returns
    -------
    list of int
        アクセス可能なコンテストの ID のリスト。ID は降順ソート。

    Raises
    ------
    Exception
        API へのリクエストが失敗した場合、またはレスポンスの内容が期待したものでない場合。
    """
    url: str = "https://codeforces.com/api/contest.list"
    response = make_request(url)

    try:
        data = response.json()
        contests = data.get("result", [])
    except ValueError as e:
        raise Exception(f"Failed to decode response from {url}") from e

    if not contests or not all("id" in contest for contest in contests):
        raise Exception(f"Unexpected response from {url}")

    # 既に終了したコンテストのみを抽出
    contests = [contest for contest in contests if contest["phase"] == "FINISHED"]
    contest_ids = sorted((contest["id"] for contest in contests), reverse=True)

    return contest_ids


def get_contest_page_content(contest_id: int):
    """
    特定のコンテストページの HTML を取得する。
    """
    contest_url: str = f"https://codeforces.com/contest/{contest_id}"
    response = make_request(contest_url)

    soup = BeautifulSoup(response.text, "html.parser")

    return soup


def get_problem_links_names(soup, contest_id: int):
    """
    特定のコンテストページに含まれる問題の URL と問題名を取得する。
    たまに、pdf で問題が出されることがあり、その場合は例外的な処理が必要。
    """
    problem_rows = soup.select("table.problems tr")
    problem_link_name = []
    for row in problem_rows[1:]:
        problem_link_elem = row.select_one("td.id a")
        if problem_link_elem:
            href = problem_link_elem.get("href")
            if href and f"/contest/{contest_id}/problem/" in href:
                problem_name_elem = row.select_one("td:nth-child(2) a")
                problem_name = (
                    problem_name_elem.text.strip() if problem_name_elem else None
                )
                problem_link_name.append(
                    (f"https://codeforces.com{href}", problem_name)
                )

    return problem_link_name


def get_solved_count(soup, contest_id: int):
    """
    特定のコンテストの各問題を解いた人数を取得する。
    """
    problem_rows = soup.select("table.problems tr")
    problem_stats_info = []
    for row in problem_rows[1:]:
        problem_link_elem = row.select_one("td.id a")
        solved_count_element = row.select_one(
            "td a[title='Participants solved the problem']"
        )
        if problem_link_elem:
            href = problem_link_elem.get("href")
            solved_count = 0
            if solved_count_element:
                solved_count = int(
                    re.search(r"x(\d+)", solved_count_element.text).group(1)
                )
            if href and f"/contest/{contest_id}/problem/" in href:
                problem_id = href.split("/")[-1]
                problem_stats_info.append(
                    {
                        "contestId": contest_id,
                        "index": problem_id,
                        "solved_count": solved_count,
                    }
                )

    return problem_stats_info


def get_problem_info(problem_url: str, problem_name: str = None):
    """
    問題ページから問題の情報を取得する。
    """
    response = make_request(problem_url)

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        raise Exception(f"Failed to parse HTML from {problem_url}") from e

    # contestId and index are directly derived from the URL
    contest_id = int(problem_url.split("/")[-3])
    index = problem_url.split("/")[-1]

    # name is derived from the problem_name argument if provided, otherwise from the problem statement header
    if not problem_name:
        try:
            problem_name = (
                soup.select_one("div.header > div.title")
                .text.strip()
                .split(".")[1]
                .strip()
            )
        except AttributeError:
            problem_name = None

    # tags are derived from the tag-box element
    try:
        tags = [tag.text.strip() for tag in soup.select(".tag-box")]
    except AttributeError:
        tags = []

    # points are extracted from the tags
    points = None
    for tag in tags:
        if tag == "*special problem":
            tags.remove(tag)
            tags.append("*special")
        if "*" in tag and tag != "*special problem" and tag != "*special":
            points = int(re.search(r"\*(\d+)", tag).group(1))
            tags.remove(tag)
            break

    problem_info = {
        "contestId": contest_id,
        "index": index,
        "name": problem_name,
        "type": "PROGRAMMING",
        "points": points,
        "tags": tags,
    }

    return problem_info


def main():
    """
    Main function to crawl and print problem data from Codeforces.
    """
    parser = argparse.ArgumentParser(description="Crawl problem data from Codeforces.")
    parser.add_argument(
        "--mode",
        choices=["all", "daily_update"],
        help="Operation mode. 'all' to fetch all problems, 'daily_update' to fetch recent problems only.",
    )
    args = parser.parse_args()

    if args.mode == "all":
        avail_contest_ids = get_avail_contest_ids()
    elif args.mode == "daily_update":
        avail_contest_ids = get_avail_contest_ids()[
            :20
        ]  # Assuming the 20 most recent contests are returned first

    all_problems_info = []
    all_problems_stats_info = []

    for contest_id in tqdm(avail_contest_ids):
        soup = get_contest_page_content(contest_id)

        problem_stats_info = get_solved_count(soup, contest_id)
        all_problems_stats_info.extend(problem_stats_info)

        problem_links_names = get_problem_links_names(soup, contest_id)
        for url, name in problem_links_names:
            all_problems_info.append(get_problem_info(url, name))
            time.sleep(SLEEP)

    if args.mode == "daily_update":
        try:
            with open("crawl_problems.json", "r") as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = {
                "status": "OK",
                "result": {"problems": [], "problemStatistics": []},
            }
        existing_problems = existing_data["result"]["problems"]
        existing_problem_stats = existing_data["result"]["problemStatistics"]

        all_problems_info = merge_problems(existing_problems, all_problems_info)
        all_problems_stats_info = merge_problem_stats(
            existing_problem_stats, all_problems_stats_info
        )

    output = {
        "status": "OK",
        "result": {
            "problems": all_problems_info,
            "problemStatistics": all_problems_stats_info,
        },
    }

    with open("./data/crawl_problems.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()
