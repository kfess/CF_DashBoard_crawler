import json


def merge_problems(api_problems, crawl_problems):
    """
    Codeforces API から取得した問題一覧と、クロールで取得した問題一覧をマージする。
    """
    api_problem_map = {
        (problem["contestId"], problem["index"]): problem for problem in api_problems
    }
    crawl_problem_map = {
        (problem["contestId"], problem["index"]): problem for problem in crawl_problems
    }

    merged_problems = []
    for key, api_problem in api_problem_map.items():
        merged_problems.append(crawl_problem_map.get(key, api_problem))

    for key, crawl_problem in crawl_problem_map.items():
        if key not in api_problem_map:
            merged_problems.append(crawl_problem)

    return merged_problems


def merge_problem_stats(api_problem_stats, crawl_problem_stats):
    """
    Codeforces API から取得した問題統計情報と、クロールで取得した問題統計情報をマージする。
    """
    api_problem_stats_map = {
        (problem["contestId"], problem["index"]): problem
        for problem in api_problem_stats
    }

    crawl_problem_stats_map = {
        (problem["contestId"], problem["index"]): problem
        for problem in crawl_problem_stats
    }

    merged_stats = []
    for key, api_stat in api_problem_stats_map.items():
        merged_stats.append(crawl_problem_stats_map.get(key, api_stat))

    for key, crawl_stat in crawl_problem_stats_map.items():
        if key not in api_problem_stats_map:
            merged_stats.append(crawl_stat)

    return merged_stats


def main():
    """
    Main function to merge problems and problem statistics.
    """
    with open("./data/api_problems.json", "r") as f:
        api_problems = json.load(f)["result"]["problems"]

    with open("./data/crawl_problems.json", "r") as f:
        crawl_problems = json.load(f)["result"]["problems"]

    with open("./data/api_problems.json", "r") as f:
        api_problem_stats = json.load(f)["result"]["problemStatistics"]

    with open("./data/crawl_problems.json", "r") as f:
        crawl_problem_stats = json.load(f)["result"]["problemStatistics"]

    merged_problems = merge_problems(api_problems, crawl_problems)
    merged_stats = merge_problem_stats(api_problem_stats, crawl_problem_stats)

    output = {
        "status": "OK",
        "result": {
            "problems": merged_problems,
            "problemStatistics": merged_stats,
        },
    }

    with open("./data/problems.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()
