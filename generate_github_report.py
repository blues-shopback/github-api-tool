import os
import csv
import argparse
from urllib.parse import urlparse
from datetime import datetime
import concurrent.futures

import github_api_utils as github_utils
from github_graphql_utils import get_repo_list_alert


OWNER = os.getenv("OWNER", "shopback")
TOKEN = os.getenv("GITHUB_TOKEN")


def _get_date_stamp():
    now = datetime.utcnow()

    return datetime.strftime(now, "%Y%m%d")


def _url_parse(url):
    u = urlparse(url)
    domain = u.netloc

    return domain


def get_commits(repo, number_commits=5):
    commit_name_date_list = []

    page_size = min(100, number_commits)
    for d in github_utils.get_repo_commits(OWNER, TOKEN, repo, page_size=page_size):
        try:
            name = d["commit"]["author"]["name"]
            date = d["commit"]["author"]["date"]
        except Exception as err:
            print("Repo: {} has err when get_repo_commits".format(repo))
            print(err)
            continue

        commit_name_date_list.append((name, date))
        if len(commit_name_date_list) >= number_commits:
            break

    return commit_name_date_list


def get_workflow_name_list(repo):
    workflow_list = []
    for d in github_utils.get_workflow_in_repo(OWNER, TOKEN, repo):
        workflow_list.append(d["name"])

    return workflow_list


def get_team_name(repo_name):
    team_name = github_utils.get_team_name(OWNER, TOKEN, repo_name)

    return team_name


def get_webhooks(repo_name):
    webhook_list = []
    for d in github_utils.get_repo_webhooks(OWNER, TOKEN, repo_name):
        url = d["config"]["url"]
        domain = _url_parse(url)
        webhook_list.append(domain)

    return webhook_list


def get_keys(repo_name):
    key_list = []
    for d in github_utils.get_repo_keys(OWNER, TOKEN, repo_name):
        key = d["key"]
        key_list.append(key)

    return key_list


def get_alert_counts(repo_name):
    return get_repo_list_alert(OWNER, TOKEN, repo_name)


def get_repo_info(repo):
    repo_name = repo["name"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(get_team_name, repo_name)
        future2 = executor.submit(get_workflow_name_list, repo_name)
        future3 = executor.submit(get_webhooks, repo_name)
        future4 = executor.submit(get_keys, repo_name)
        future5 = executor.submit(get_alert_counts, repo_name)

        team_name = future1.result()
        workflow_list = future2.result()
        webhook_list = future3.result()
        key_list = future4.result()
        alert_counts = future5.result()

    workflow_count = len(workflow_list)
    webhook_count = len(webhook_list)
    key_count = len(key_list)

    # build info dict
    repo_info = {
        "name": repo_name,
        "team": team_name,
        "keyCount": key_count,
        "workflowCount": workflow_count,
        "webhookCount": webhook_count,
        "workflowNames": ",".join(workflow_list),
        "webhookNames": ",".join(webhook_list),
        "alertCount_CRITICAL_FIXED": alert_counts["CRITICAL_FIXED"],
        "alertCount_HIGH_FIXED": alert_counts["HIGH_FIXED"],
        "alertCount_MODERATE_FIXED": alert_counts["MODERATE_FIXED"],
        "alertCount_LOW_FIXED": alert_counts["LOW_FIXED"],
        "alertCount_CRITICAL_OPEN": alert_counts["CRITICAL_OPEN"],
        "alertCount_HIGH_OPEN": alert_counts["HIGH_OPEN"],
        "alertCount_MODERATE_OPEN": alert_counts["MODERATE_OPEN"],
        "alertCount_LOW_OPEN": alert_counts["LOW_OPEN"],
     }

    return repo_info


def generate_github_report(args):
    test_limit = args.test_limit
    org_info = github_utils._get_org_info(OWNER, TOKEN)
    total_repo_count = org_info["public_repos"] + org_info["total_private_repos"]
    repo_info_list = []
    print("Owner:", OWNER)
    print("Token:", TOKEN)
    if args.orphan_report:
        print("Generate orphan commits report.")
        orphan_data = {}
    print("Get repo data. total: {}".format(
        total_repo_count))

    for i, repo in enumerate(github_utils.get_repo_data(OWNER, TOKEN)):
        print("Progress: {:>4}/{:>4}".format(i+1, total_repo_count), end="\r")
        repo_info = get_repo_info(repo)
        repo_info_list.append(repo_info)

        if args.orphan_report:
            if repo_info["team"] is None and repo["archived"] is False:
                repo_name = repo_info["name"]
                name_date_list = get_commits(repo_name)
                orphan_data[repo_name] = name_date_list

        if test_limit:
            i += 1
            if i >= test_limit:
                print("Break by test_limit={}".format(test_limit))
                break
    date_stamp = _get_date_stamp()
    filename = "github_report_{}.csv".format(date_stamp)
    with open(os.path.join(args.output, filename), "w") as f:
        fieldnames = repo_info_list[0].keys()
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()

        for info in repo_info_list:
            writer.writerow(info)
    if args.orphan_report:
        fields = ["repo_name", "author1", "date1", "author2", "date2", "author3", "date3",
                  "author4", "date4", "author5", "date5"]
        orphan_filename = "github_orphan_report_{}.csv".format(date_stamp)
        with open(os.path.join(args.output, orphan_filename), "w") as f:
            writer = csv.DictWriter(f, fields)
            writer.writeheader()
            for repo, authors in orphan_data.items():
                row_dict = {"repo_name": repo}
                for i, (name, date) in enumerate(authors):
                    keyname1 = "author{}".format(i+1)
                    keyname2 = "date{}".format(i+1)
                    row_dict[keyname1] = name
                    row_dict[keyname2] = date
                writer.writerow(row_dict)

    print("Generate github report at: {}".format(os.path.join(args.output, filename)))
    if args.orphan_report:
        print("Generate github orphan report at: {}".format(
            os.path.join(args.output, orphan_filename)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="github scan tool.")
    parser.add_argument('-o', '--output', default='', type=str,
                        help='output report director.')
    parser.add_argument('--orphan_report', action='store_true', help='Generate orphan report.')
    parser.add_argument('--test_limit', default=0, type=int, help='Test run limit.')
    args = parser.parse_args()
    generate_github_report(args)
