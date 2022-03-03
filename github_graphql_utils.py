from collections import Counter
from string import Template

import requests


graphql_endpoint = "https://api.github.com/graphql"
alert_query_str = """
{
    repository(name: "$repo", owner: "$owner") {
        vulnerabilityAlerts($first, $after) {
            pageInfo {
                endCursor
                startCursor
            }
            nodes {
                state
                id
                createdAt
                dismissedAt
                securityVulnerability {
                    package {
                        name
                    }
                    severity
                }
            }
        }
    }
}
"""


def _get_token_header(token):
    return {"Authorization": "bearer {}".format(token)}


def _count_alert_severity(nodes):
    counter = Counter()
    id_set = set()
    for node in nodes:
        severity = node["securityVulnerability"]["severity"]
        state = node["state"]
        key = "_".join([severity, state])
        counter[key] += 1
        id_set.add(node["id"])

    return counter, id_set


def get_repo_list_alert(owner, token, repo, batch_num=100):
    headers = _get_token_header(token)
    query_str = Template(alert_query_str).substitute(
        first="first: {}".format(batch_num),
        after="",
        repo=repo,
        owner=owner
    )
    res = requests.post(
        graphql_endpoint,
        headers=headers,
        json={"query": query_str}
    )

    data = res.json()
    endCursor = data["data"]["repository"]["vulnerabilityAlerts"]["pageInfo"]["endCursor"]

    severity_counter = Counter()
    node_id_set = set()  # check node id num
    while endCursor is not None:
        nodes = data["data"]["repository"]["vulnerabilityAlerts"]["nodes"]
        counter, id_set = _count_alert_severity(nodes)
        severity_counter += counter
        node_id_set.update(id_set)

        query_str = Template(alert_query_str).substitute(
            first="first: {}".format(batch_num),
            after="after: \"{}\"".format(endCursor),
            repo=repo,
            owner=owner
        )
        res = requests.post(
            graphql_endpoint,
            headers=headers,
            json={"query": query_str}
        )
        data = res.json()
        endCursor = data["data"]["repository"]["vulnerabilityAlerts"]["pageInfo"]["endCursor"]

    # check final count number and node id number.
    assert len(node_id_set) == sum(severity_counter.values()), \
        "node_id_set: {}, severity_counter: {}".format(
            len(node_id_set),
            sum(severity_counter.values())
        )

    return severity_counter
