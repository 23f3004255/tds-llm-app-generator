import os
import base64
from github import Github, GithubException
from github import InputGitTreeElement
from typing import Dict, Any, List
from dotenv import load_dotenv
import requests
import time
from app.logger import get_logger

log = get_logger(__name__)

load_dotenv()

# Environment Variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = os.getenv("GITHUB_USERNAME")

# Authenticate once
g = Github(GITHUB_TOKEN)
user = g.get_user()


def create_repo(repo_name: str):
    log.info(f"Creating repository: {repo_name}")
    # log.info("TOKEN:", GITHUB_TOKEN[:8], "...", "OWNER:", OWNER)

    try:
        repo = user.create_repo(
            name=repo_name,
            private=False,
            auto_init=True,
            description=f"Auto-generated repo for task {repo_name}"
        )
        log.info("Repository created:", repo.full_name)
        return repo
    except GithubException as e:
        if e.status == 422:  # repo already exists
            log.info("Repo already exists.")
            return g.get_repo(f"{OWNER}/{repo_name}")
        else:
            raise e


# def commit_file(repo, file_path: str, content_bytes: bytes, commit_msg: str):
#     log.info(f"Committing file: {file_path}")
#     try:
#         # Check if file exists
#         contents = repo.get_contents(file_path)
#         repo.update_file(contents.path, commit_msg, content_bytes.decode("utf-8"), contents.sha)
#         log.info(f"Updated: {file_path}")
#     except GithubException as e:
#         if e.status == 404:
#             repo.create_file(file_path, commit_msg, content_bytes.decode("utf-8"))
#             log.info(f"Created: {file_path}")
#         else:
#             raise e

def commit_file(repo, file_path: str, content_bytes: bytes, commit_msg: str):
    log.info(f"Committing file: {file_path}")
    try:
        # Check if file exists
        contents = repo.get_contents(file_path)
        result = repo.update_file(contents.path, commit_msg, content_bytes.decode("utf-8"), contents.sha)
        sha = result["commit"].sha  # Get the commit SHA
        log.info(f"Updated: {file_path} (SHA: {sha})")
        return sha
    except GithubException as e:
        if e.status == 404:
            result = repo.create_file(file_path, commit_msg, content_bytes.decode("utf-8"))
            sha = result["commit"].sha  # Get the commit SHA
            log.info(f"Created: {file_path} (SHA: {sha})")
            return sha
        else:
            raise e
        

def commit_all_files_single_sha(repo, files: list, commit_msg: str):
    """
    Commit multiple files in a single commit and return the commit SHA.
    """
    # Get main branch reference
    ref = repo.get_git_ref("heads/main")
    base_commit = repo.get_git_commit(ref.object.sha)

    # Create blobs for all files
    element_list = []
    for f in files:
        blob = repo.create_git_blob(f["content"], "utf-8")
        element_list.append({
            "path": f["path"],
            "mode": "100644",
            "type": "blob",
            "sha": blob.sha
        })

    # Create tree
    tree = repo.create_git_tree(element_list, base_commit.tree)

    # Create commit
    commit = repo.create_git_commit(commit_msg, tree, [base_commit])

    # Update branch reference
    ref.edit(commit.sha)

    log.info(f"Committed all files in one commit: SHA {commit.sha}")
    return commit.sha




def enable_github_pages(repo_name, token, owner):
    """
    Enables GitHub Pages for a repo using REST API (2025 method).
    Works after initial commits are pushed to 'main'.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    # Step 1: Check if repo exists and has main branch
    repo_url = f"https://api.github.com/repos/{owner}/{repo_name}/branches/main"
    r = requests.get(repo_url, headers=headers)
    if r.status_code != 200:
        log.info("'main' branch not found. Retrying in 5s...")
        time.sleep(5)
        r = requests.get(repo_url, headers=headers)
        if r.status_code != 200:
            log.info(f"Could not find main branch: {r.status_code} {r.text}")
            return None

    # Step 2: Wait briefly so commits are fully registered
    time.sleep(3)

    # Step 3: Configure Pages to use / (root) of main branch
    pages_url = f"https://api.github.com/repos/{owner}/{repo_name}/pages"
    data = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }

    response = requests.post(pages_url, json=data, headers=headers)

    if response.status_code in [201, 204]:
        final_url = f"https://{owner}.github.io/{repo_name}/"
        log.info(f"GitHub Pages enabled: {final_url}")
        return final_url
    else:
        log.info(f"Failed to enable GitHub Pages: {response.status_code} {response.text}")

        # Step 4️⃣: Fallback (retry with gh-pages branch)
        if response.status_code == 404:
            log.info("Retrying with 'gh-pages' branch fallback...")
            fallback_data = {
                "source": {
                    "branch": "gh-pages",
                    "path": "/"
                }
            }
            response2 = requests.post(pages_url, json=fallback_data, headers=headers)
            if response2.status_code in [201, 204]:
                final_url = f"https://{owner}.github.io/{repo_name}/"
                log.info(f"GitHub Pages enabled via gh-pages: {final_url}")
                return final_url
            else:
                log.info(f"Still failed: {response2.status_code} {response2.text}")
        return None




# def handle_round(task_id: str, round_number: int, generated_files: List[Dict[str, str]]):
#     repo_name = f"task-{task_id}"

#     # Round 1: Create repo (without enabling Pages yet)
#     if round_number == 1:
#         repo = create_repo(repo_name)
#     else:
#         repo = g.get_repo(f"{OWNER}/{repo_name}")

#     # Step 1: Commit all files
#     sha_dict = {}
#     # for f in generated_files:
#     #     path = f["path"]
#     #     content = f["content"].encode("utf-8")
#     #     commit_file(repo, path, content, f"Round {round_number} commit")
#     #     sha_dict[path] = "committed"

#     for f in generated_files:
#         path = f["path"]
#         content = f["content"].encode("utf-8")
#         commit_sha = commit_file(repo, path, content, f"Round {round_number} commit")
#         sha_dict[path] = commit_sha

#     # Step 2: Enable Pages only after committing files (branch exists now)
#     pages_url = None
#     if round_number == 1:
#         pages_url = enable_github_pages(repo_name=repo_name, token=GITHUB_TOKEN, owner=OWNER)

#     return {"repo": repo_name, "commit_shas": sha_dict, "pages_url": pages_url}


def handle_round(task_id: str, round_number: int, generated_files: List[Dict[str, str]]):
    repo_name = f"task-{task_id}"

    # Round 1: create repo (auto-init)
    if round_number == 1:
        repo = create_repo(repo_name)
    else:
        repo = g.get_repo(f"{OWNER}/{repo_name}")

    # Commit all files in one commit per round
    commit_sha = commit_all_files_single_sha(
        repo,
        files=[{"path": f["path"], "content": f["content"]} for f in generated_files],
        commit_msg=f"Round {round_number} commit"
    )

    # Map all files to same SHA
    sha_dict = {f["path"]: commit_sha for f in generated_files}

    # Enable Pages only in round 1 (after all files committed)
    pages_url = None
    if round_number == 1:
        pages_url = enable_github_pages(repo_name=repo_name, token=GITHUB_TOKEN, owner=OWNER)

    return {"repo": repo_name, "commit_shas": sha_dict, "pages_url": pages_url}




def commit_all_files_single_sha(repo, files: list, commit_msg: str):
    """
    Commit multiple files in a single commit and return the commit SHA.
    """
    # 1 Get main branch reference
    ref = repo.get_git_ref("heads/main")
    base_commit = repo.get_git_commit(ref.object.sha)

    # 2 Create blobs and InputGitTreeElement for each file
    element_list = []
    for f in files:
        blob = repo.create_git_blob(f["content"], "utf-8")
        element_list.append(InputGitTreeElement(f["path"], "100644", "blob", sha=blob.sha))

    # 3 Create tree
    tree = repo.create_git_tree(element_list, base_commit.tree)

    # 4 Create commit
    commit = repo.create_git_commit(commit_msg, tree, [base_commit])

    # 5 Update branch reference
    ref.edit(commit.sha)

    log.info(f"Committed all files in one commit: SHA {commit.sha}")
    return commit.sha


# def push_to_github(task_id: str, round_number: int, base_dir: str = "generated_app") -> Dict[str, Any]:
#     generated_files = []
#     for root, dirs, files in os.walk(base_dir):
#         for f in files:
#             file_path = os.path.join(root, f)
#             rel_path = os.path.relpath(file_path, base_dir)
#             with open(file_path, "rb") as file_obj:
#                 try:
#                     content = file_obj.read().decode("utf-8")
#                 except UnicodeDecodeError:
#                     content = base64.b64encode(file_obj.read()).decode("utf-8")
#             generated_files.append({"path": rel_path, "content": content})

#     try:
#         task_id = task_id.replace(" ", "_").strip()
#         response = handle_round(task_id, round_number, generated_files)
#     except Exception as e:
#         log.info(f" Error in handle_round: {e}")
#         response = {}

#     return response

def push_to_github(task_id: str, round_number: int, base_dir: str = "generated_app") -> Dict[str, Any]:
    """
    Push all files from the generated app folder to GitHub in a single commit per round.
    Returns:
        {
            "repo_name": str,
            "commit_sha": str,
            "pages_url": Optional[str]
        }
    """
    generated_files = []

    # Step 1: Read all files from the generated directory
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path, base_dir)
            with open(file_path, "rb") as file_obj:
                try:
                    content = file_obj.read().decode("utf-8")
                except UnicodeDecodeError:
                    content = base64.b64encode(file_obj.read()).decode("utf-8")
            generated_files.append({"path": rel_path, "content": content})

    # Step 2: Clean task_id
    task_id = task_id.replace(" ", "_").strip()

    # Step 3: Handle the round
    try:
        result = handle_round(task_id, round_number, generated_files)

        # Extract a single commit SHA (all files committed in one commit)
        commit_sha = None
        if result.get("commit_shas"):
            commit_sha = list(result["commit_shas"].values())[0]

        return {
            "repo_name": result.get("repo"),
            "commit_sha": commit_sha,
            "pages_url": result.get("pages_url")
        }

    except Exception as e:
        log.info(f"Error in handle_round: {e}")
        return {
            "repo_name": None,
            "commit_sha": None,
            "pages_url": None
        }

