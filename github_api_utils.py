import requests


def _find_next_link(headers):
    if "link" not in headers:
        return None
    for d in requests.utils.parse_header_links(headers["link"]):
        if d["rel"] == "next":
            return d["url"]


def _get_list_data_scroll(token, url, data_proc_fn=None, page_size=100):
    params = {
        "access_token": token,
        "per_page": page_size,
        "page": 1}
    res = requests.get(
        url,
        params=params)
    # If status code is not 200, return.
    if res.status_code != 200:
        return None
    if data_proc_fn is not None:
        data_list = data_proc_fn(res.json())
    else:
        data_list = res.json()
    for d in data_list:
        yield d

    next_link = _find_next_link(res.headers)
    while next_link:
        res = requests.get(next_link)
        res.raise_for_status()
        if data_proc_fn is not None:
            data_list = data_proc_fn(res.json())
        else:
            data_list = res.json()
        for d in data_list:
            yield d
        next_link = _find_next_link(res.headers)


def get_repo_webhooks(org, token, repo):
    """Get all repo data from 'https://api.github.com/repos/{owner}/{repo}/hooks'

    Args:
        org: organization name.
        token: access_token.

    Return:
        iterable dicts.
    """
    url = "https://api.github.com/repos/{}/{}/hooks".format(org, repo)
    for d in _get_list_data_scroll(token, url):
        yield d


def get_repo_commits(org, token, repo, page_size=5):
    """Get all repo data from 'https://api.github.com/repos/{org}/{repo}/commits'

    Args:
        org: organization name.
        token: access_token.
        repo: repo name.

    Return:
        list of dict. Each dict is a commit information.
    """
    url = "https://api.github.com/repos/{}/{}/commits".format(org, repo)
    for d in _get_list_data_scroll(token, url, page_size=page_size):
        yield d


def get_repo_data(org, token):
    """Get all repo data from 'https://api.github.com/orgs/{org}/repos'

    Args:
        org: organization name.
        token: access_token.

    Return:
        list of dict. Each dict is a repo's information.
    """
    url = "https://api.github.com/orgs/{}/repos".format(org)
    for d in _get_list_data_scroll(token, url):
        yield d


def get_team_name(org, token, repo):
    """Get repo admin team name from 'https://api.github.com/repos/{owner}/{repo}/teams'

    Args:
        org: organization name.
        token: access_token.
        repo: repo name.

    Return:
        string, team name for repo admin.
    """
    url = "https://api.github.com/repos/{}/{}/teams".format(org, repo)
    for team in _get_list_data_scroll(token, url):
        if team["permission"] == "admin":
            return team["name"]


def repo_has_alert_setting(org, token, repo):
    """Get alert setting for repo.

    Args:
        org: organization name.
        token: access_token.
        repo: repo name.

    Return:
        bool, indicate repo has alerts setting or not.
    """
    params = {"access_token": token}
    headers = {"Accept": "application/vnd.github.dorian-preview+json"}
    res = requests.get(
        "https://api.github.com/repos/{}/{}/vulnerability-alerts".format(
            org, repo),
        params=params,
        headers=headers)
    if res.status_code == 204:
        return True
    else:
        return False


def _get_org_info(org, token):
    params = {"access_token": token}
    url = "https://api.github.com/orgs/{}".format(org)
    res = requests.get(
        url,
        params=params)
    if res.status_code == 200:
        return res.json()


def repo_has_protected_branch(org, token, repo):
    """Get all brances info from repo.

    Args:
        org: organization name.
        token: access_token.
        repo: repo name.

    Return:
        bool, indicate repo has at last one protected branch or not.
    """
    url = "https://api.github.com/repos/{}/{}/branches".format(org, repo)
    for branch in _get_list_data_scroll(token, url):
        if branch["protected"] is True:
            return True
    return False


def get_repo_keys(org, token, repo):
    """Get all repo data from 'https://api.github.com/repos/{owner}/{repo}/keys'

    Args:
        org: organization name.
        token: access_token.
        repo: repo name.

    Return:
        list of dict. Each dict is a repo's key info.
    """
    url = "https://api.github.com/repos/{}/{}/keys".format(org, repo)
    for d in _get_list_data_scroll(token, url):
        yield d


def get_repo_files(org, token, repo, director):
    """Get files info under director.

    Args:
        org: organization name.
        token: access_token.
        repo: repo name.
        director: director path.

    Return:
        list of dict. Each dict is a file's information.
    """
    params = {"access_token": token}
    res = requests.get(
        "https://api.github.com/repos/{}/{}/contents/{}".format(
            org, repo, director),
        params=params)
    if res.status_code == 200:
        data = []
        for d in res.json():
            data.append(d)
        return data
    else:
        return None


def get_github_config(org, token, repo, director):
    """Get github config under director. Check pull request template and code owner.

    Args:
        org: organization name.
        token: access_token.
        repo: repo name.
        director: director path.

    Return:
        dict.
    """
    hasPullRequestTemplate = False
    hasCodeOwner = False
    files = get_repo_files(org, token, repo, director)
    if not files:
        return {"hasPullRequestTemplate": hasPullRequestTemplate,
                "hasCodeOwner": hasCodeOwner}
    for f in files:
        name = f["name"]
        lower_name = name.lower()
        if "pull_request_template" in lower_name:
            hasPullRequestTemplate = True
        if "codeowners" in lower_name:
            hasCodeOwner = True

    return {"hasPullRequestTemplate": hasPullRequestTemplate,
            "hasCodeOwner": hasCodeOwner}


def get_has_readme(org, token, repo):
    params = {"access_token": token}
    res = requests.get("https://api.github.com/repos/{}/{}/readme".format(org, repo),
                       params=params)
    if res.status_code != 200:
        return False
    else:
        return True


def get_org_webhooks(org, token):
    """Get repo webhooks from 'https://api.github.com/repos/{}/{}/hooks'

    Args:
        org: organization name.
        token: access_token.

    Return:
        interger, number of webhooks in api returns.
    """
    url = "https://api.github.com/orgs/{}/hooks".format(org)
    data = []
    for d in _get_list_data_scroll(token, url):
        data.append(d)

    return data


def get_workflow_in_repo(org, token, repo):
    """Get repo workflows from 'https://api.github.com/repos/{owner}/{repo}/actions/workflows'

    Args:
        org: organization name.
        repo: repo names.
        token: access_token.

    Return:
        list of dict. Each dict is a repo's workflow information.
    """
    url = "https://api.github.com/repos/{}/{}/actions/workflows".format(org, repo)
    data = []

    for d in _get_list_data_scroll(token, url, lambda x: x["workflows"]):
        data.append(d)

    return data
