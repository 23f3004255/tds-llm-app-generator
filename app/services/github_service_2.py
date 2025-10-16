import os
import base64
from github import Github, GithubException
from typing import Dict, Any, List
from dotenv import load_dotenv
import requests
import time

load_dotenv()

# Environment Variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = os.getenv("GITHUB_USERNAME")

# Authenticate once
g = Github(GITHUB_TOKEN)
user = g.get_user()


def create_repo(repo_name: str):
    print("🔹 Creating repository:", repo_name)
    print("TOKEN:", GITHUB_TOKEN[:8], "...", "OWNER:", OWNER)

    try:
        repo = user.create_repo(
            name=repo_name,
            private=False,
            auto_init=True,
            description=f"Auto-generated repo for task {repo_name}"
        )
        print("✅ Repository created:", repo.full_name)
        return repo
    except GithubException as e:
        if e.status == 422:  # repo already exists
            print("⚠️ Repo already exists.")
            return g.get_repo(f"{OWNER}/{repo_name}")
        else:
            raise e


def commit_file(repo, file_path: str, content_bytes: bytes, commit_msg: str):
    print(f"📦 Committing file: {file_path}")
    try:
        # Check if file exists
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, commit_msg, content_bytes.decode("utf-8"), contents.sha)
        print(f"✅ Updated: {file_path}")
    except GithubException as e:
        if e.status == 404:
            repo.create_file(file_path, commit_msg, content_bytes.decode("utf-8"))
            print(f"✅ Created: {file_path}")
        else:
            raise e


# def enable_pages(repo, branch="main"):
#     print("🌐 Enabling GitHub Pages...")
#     try:
#         repo.enable_pages(source="main")
#         print("✅ Pages enabled:", repo.html_url.replace("github.com", "github.io"))
#         return repo.html_url.replace("github.com", "github.io")
#     except Exception as e:
#         raise Exception(f"Failed to enable GitHub Pages: {e}")
    
# def enable_github_pages(repo_name, token, owner):
#     """
#     Safely enables GitHub Pages for an existing repo after ensuring main branch exists.
#     """
#     url = f"https://api.github.com/repos/{owner}/{repo_name}/pages"
#     headers = {
#         "Authorization": f"token {token}",
#         "Accept": "application/vnd.github+json",
#     }

#     data = {
#         "source": {
#             "branch": "main",
#             "path": "/"
#         }
#     }

#     # Wait a bit to ensure repo + commits exist
#     time.sleep(3)

#     response = requests.put(url, json=data, headers=headers)

#     if response.status_code in [201, 204]:
#         print(f"✅ GitHub Pages enabled: https://{owner}.github.io/{repo_name}/")
#         return f"https://{owner}.github.io/{repo_name}/"
#     else:
#         print(f"❌ Failed to enable GitHub Pages: {response.status_code} {response.text}")
#         return None



def enable_github_pages(repo_name, token, owner):
    """
    Enables GitHub Pages for a repo using REST API (2025 method).
    Works after initial commits are pushed to 'main'.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    # Step 1️⃣: Check if repo exists and has main branch
    repo_url = f"https://api.github.com/repos/{owner}/{repo_name}/branches/main"
    r = requests.get(repo_url, headers=headers)
    if r.status_code != 200:
        print("❌ 'main' branch not found. Retrying in 5s...")
        time.sleep(5)
        r = requests.get(repo_url, headers=headers)
        if r.status_code != 200:
            print(f"❌ Could not find main branch: {r.status_code} {r.text}")
            return None

    # Step 2️⃣: Wait briefly so commits are fully registered
    time.sleep(3)

    # Step 3️⃣: Configure Pages to use / (root) of main branch
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
        print(f"✅ GitHub Pages enabled: {final_url}")
        return final_url
    else:
        print(f"❌ Failed to enable GitHub Pages: {response.status_code} {response.text}")

        # Step 4️⃣: Fallback (retry with gh-pages branch)
        if response.status_code == 404:
            print("⚠️ Retrying with 'gh-pages' branch fallback...")
            fallback_data = {
                "source": {
                    "branch": "gh-pages",
                    "path": "/"
                }
            }
            response2 = requests.post(pages_url, json=fallback_data, headers=headers)
            if response2.status_code in [201, 204]:
                final_url = f"https://{owner}.github.io/{repo_name}/"
                print(f"✅ GitHub Pages enabled via gh-pages: {final_url}")
                return final_url
            else:
                print(f"❌ Still failed: {response2.status_code} {response2.text}")
        return None




def handle_round(task_id: str, round_number: int, generated_files: List[Dict[str, str]]):
    repo_name = f"task-{task_id}"

    # Round 1: Create repo (without enabling Pages yet)
    if round_number == 1:
        repo = create_repo(repo_name)
    else:
        repo = g.get_repo(f"{OWNER}/{repo_name}")

    # Step 1: Commit all files
    sha_dict = {}
    for f in generated_files:
        path = f["path"]
        content = f["content"].encode("utf-8")
        commit_file(repo, path, content, f"Round {round_number} commit")
        sha_dict[path] = "committed"

    # Step 2: Enable Pages only after committing files (branch exists now)
    pages_url = None
    if round_number == 1:
        pages_url = enable_github_pages(repo_name=repo_name, token=GITHUB_TOKEN, owner=OWNER)

    return {"repo": repo_name, "commit_shas": sha_dict, "pages_url": pages_url}



def push_to_github(task_id: str, round_number: int, base_dir: str = "generated_app") -> Dict[str, Any]:
    generated_files = []
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

    try:
        response = handle_round(task_id, round_number, generated_files)
    except Exception as e:
        print(f"❌ Error in handle_round: {e}")
        response = {}

    return response
