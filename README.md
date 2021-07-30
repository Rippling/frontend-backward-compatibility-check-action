# Frontend Backward Compatibility Check On PRs

Checks if a PR needs a rebase with master after a merge in master.

## How to use
```
name: Validate if PR is backward compatible
on:
  pull_request:
    branches:
      - master
    types: [closed]
jobs:
  check-pr-backward-compatibility:
    if: ${{ github.event.pull_request.merged }}
    runs-on: ubuntu-latest
    steps:
      - run: echo "This action validates the code age and the release version. If failed, rebase the branch with master and push."
      - name: Checkout actions/checkout@v2
        uses: actions/checkout@v2
      - name: Check backward compatability on prs
        uses: Rippling/frontend-backward-compatibility-check-action@master
        env:
          FRONTEND_REPOSITORY: "rippling-webapp"
          GITHUB_ACTION_ID: "<action-id>"
          GIT_ACCESS_TOKEN:  "${{ secrets.JENKINS_GIT_ACCESS_TOKEN }}"

```
