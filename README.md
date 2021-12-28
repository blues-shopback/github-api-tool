# github-api-tool
Get information from GitHub using GitHub-Api.

## Usage
Using github token to crawl repo information.

### Get Github Token
1. Go to https://github.com/settings/tokens, then click `Generate new token`.
2. Note what is this token about in `Note`.
3. Select ALL repo permission in `Select scopes`.
4. Click `Generate token` in the bottom of page.
5. Write down the token, it only shows once.

### Generate Report
Add your github token to env:

    export GITHUB_TOKEN=your-github-token

Go to repo directory

    cd github-api-tool

Start generate reports:

    python3 generate_github_report.py --output output-dir-path

Note:
- output directory needs created in advance.
- Test run few repo with flag. ex: add flag `--test_limit 3` will run for 3 repo.
