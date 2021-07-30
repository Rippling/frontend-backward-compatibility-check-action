import logging
import os
import requests
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from multiprocessing import Pool, cpu_count
import time

start_time = time.time()

logging.getLogger().setLevel(logging.INFO)

def trigger_backward_compatibility_check_workflow_for_pr(edge):
    github_action_id = os.getenv('GITHUB_ACTION_ID')
    repository = os.getenv('FRONTEND_REPOSITORY')
    url = 'https://api.github.com/repos/Rippling/{}/actions/workflows/{}/dispatches'.format(repository, github_action_id)
    pr = edge['node']
    branch_name = pr['headRefName']
    pr_number = pr['number']
    logging.info("Triggering build for pr: {}".format(pr_number))
    api_token = os.getenv("GIT_ACCESS_TOKEN")
    json = {"ref": branch_name}
    headers = {'Authorization': 'token {}'.format(api_token)}
    logging.info("Triggering workflow for branch {}".format(branch_name))
    response = requests.post(url=url, json=json, headers=headers)
    if not response.ok:
        logging.error("Error while triggering backward compatibility check workflow for branch {}".format(branch_name))
        logging.error(response.content)
    return response


def get_pr_data_from_github(repository, today):
    url = 'https://api.github.com/graphql'
    api_token = os.getenv("GIT_ACCESS_TOKEN")
    headers = {'Authorization': 'token {}'.format(api_token)}
    json = {'query': get_query_to_fetch_frontend_prs_created_after(repository, today)}
    r = requests.post(url=url, json=json, headers=headers)
    data = (r.json())
    return data


def get_output_line_dict_from_PR_dict(pr_dict, repository):
    last_commit = pr_dict['commits']['nodes'][0]['commit']

    status = last_commit.get('status', None)

    # value of the key status could be None by itself

    if status:
        context = status.get('context', {'description': 'No status found for pr'})
    else:
        context = {'description': 'No status found for pr'}

    did_run_tests = bool(context)
    did_tests_pass = None
    if did_run_tests:
        did_tests_pass = context['description'] == 'This commit looks good'
    github_repo_pr_stats = GithubRepoPrStats(title=pr_dict["title"],
                                             url=pr_dict["url"],
                                             author=pr_dict["mergedBy"]["login"],
                                             merged_at=pr_dict["mergedAt"],
                                             repository=repository,
                                             did_run_integration_tests=did_run_tests,
                                             did_pass_naturally=did_tests_pass)
    return github_repo_pr_stats


def get_query_to_fetch_frontend_prs_created_after(repository, time_from):
    logging.info("Getting the query for {} to get PRs created after: {}".format(repository, time_from))
    query = '''
                {
                  search(query: "repo:rippling/%s is:pr is:open created:>%s sort:created-asc", type: ISSUE, last: 100) {
                    edges {
                      node {
                        ... on PullRequest {
                          number,
                          headRefName,
                          createdAt
                        }
                      }
                    }
                  }
                }
            ''' % (repository, time_from)
    return query


def parallel_process_prs(pull_requests_edges):
    no_of_processes = cpu_count()
    print("Total number of parallel processes: {}".format(no_of_processes))
    pool = Pool(processes=no_of_processes)
    pool.map(trigger_backward_compatibility_check_workflow_for_pr, pull_requests_edges)


def process_open_prs(repository):
    created_after = (datetime.today() - timedelta(days=16)).strftime('%Y-%m-%d')
    all_pull_requests_edges = []
    while True:
        data = get_pr_data_from_github(repository, created_after)

        pull_requests_edges = data['data']['search']['edges']

        if not pull_requests_edges:
            logging.info("No more open PRs to be processed.")
            break
        all_pull_requests_edges.extend(pull_requests_edges)
        last_fetched_pr = pull_requests_edges[len(pull_requests_edges) - 1]['node']
        created_after = last_fetched_pr['createdAt']
    print("Total number of open PRs to check for backward compatibility: {}".format(len(all_pull_requests_edges)))
    parallel_process_prs(all_pull_requests_edges)


if __name__ == "__main__":
    try:
        frontend_repository = os.getenv("FRONTEND_REPOSITORY")
        process_open_prs(frontend_repository)
        print("--- %s seconds ---" % (time.time() - start_time))
    except:
        logging.exception("Failed to PR stats.")
        raise