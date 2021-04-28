import requests
import os
from mlrun import DataItem, get_run_db, mlconf


def pr_comment(
    context, repo: str, issue: int, message: str = "", message_file: DataItem = None
):

    token = context.get_secret("GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if message_file and not message:
        message = message_file.get()
    elif not message and not message_file:
        raise ValueError("pr message or message file must be provided")

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    url = f"https://api.github.com/repos/{repo}/issues/{issue}/comments"

    resp = requests.post(url=url, json={"body": str(message)}, headers=headers)
    if not resp.ok:
        errmsg = f"bad pr comment resp!!\n{resp.text}"
        context.logger.error(errmsg)
        raise IOError(errmsg)


def run_summary_comment(context, workflow_id, repo: str, issue: int, project=""):
    db = get_run_db().connect()
    project = project or context.project
    runs = db.list_runs(project=project, labels=f"workflow={workflow_id}")

    had_errors = i = 0
    for r in runs:
        name = r["metadata"]["name"]
        if r["status"].get("state", "") == "error":
            had_errors += 1
        if name == context.name:
            del runs[i]
        i += 1

    print("errors:", had_errors)

    html = "### Run Results\nWorkflow {} finished with {} errors".format(
        workflow_id, had_errors
    )
    html += "<br>click the hyper links below to see detailed results<br>"
    html += runs.show(display=False, short=True)
    if repo:
        pr_comment(context, repo, issue, html)
    else:
        print("repo not defined")
        print(html)
