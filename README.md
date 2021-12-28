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

### Install Dependency
    pip3 install requests

### Generate Report
Add your github token to env:

    export GITHUB_TOKEN=your-github-token

Create output directory:

    mkdir path/to/output/dir

Go to repo directory

    cd github-api-tool

Start generate reports:

    python3 generate_github_report.py --output path/to/output/dir

Note:
- Output directory needs created in advance.
- Test run few repo with flag `test_limit`. ex: add flag `--test_limit 3` will run only for 3 repo.
