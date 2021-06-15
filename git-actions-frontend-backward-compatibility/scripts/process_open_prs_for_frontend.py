import logging
import os
import requests
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from multiprocessing import Pool, cpu_count
import time

start_time = time.time()

logging.getLogger().setLevel(logging.INFO)


def get_jenkins_job_url_for_pr(pr_number, job_name):
    JENKINS_URL = os.getenv("JENKINS_URL")
    return "{}job/{}/job/PR-{}/build".format(JENKINS_URL, job_name, pr_number)


def trigger_jenkins_release_validator_job_for_pr(edge):
    pr = edge['node']
    pr_number = pr['number']
    job_name = os.getenv("FRONTEND_RELEASE_VALIDATOR_JOB")
    url = get_jenkins_job_url_for_pr(pr_number, job_name)
    logging.info("Triggering build for pr: {}".format(url))
    jenkins_api_user = os.getenv("JENKINS_API_USER")
    jenkins_api_token = os.getenv("JENKINS_API_TOKEN")
    auth = HTTPBasicAuth(jenkins_api_user, jenkins_api_token)
    return requests.post(url=url, auth=auth)


def get_pr_data_from_github(repository, today):
    url = 'https://api.github.com/graphql'
    api_token = os.getenv("JENKINS_GIT_ACCESS_TOKEN")
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
                          createdAt,
                          number,
                          url
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
    pool.map(trigger_jenkins_release_validator_job_for_pr, pull_requests_edges)


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
