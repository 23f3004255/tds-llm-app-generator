import os, base64, requests
from typing import Dict, Any, List
from app.logger import get_logger

log = get_logger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = os.getenv("GITHUB_USERNAME")

def create_repo(repo_name):
    log.info("repo creation started")
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    data = {"name": repo_name, "private": False, "auto_init": False}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 201:
        return True
    elif resp.status_code == 422:
        # Repo exists
        return False
    else:
        raise Exception(resp.json())    

def commit_file(repo_name, file_path, content_bytes, commit_msg):
    log.info("commit started")
    url = f"https://api.github.com/repos/{OWNER}/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    content_b64 = base64.b64encode(content_bytes).decode()
    data = {"message": commit_msg, "content": content_b64}

    # check if file exists to include SHA for update
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        data["sha"] = get_resp.json()["sha"]

    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code in (200, 201):
        return resp.json()["commit"]["sha"]
    else:
        raise Exception(resp.json())
    

def enable_pages(repo_name, branch="main"):
    log.info("enable pages started")
    url = f"https://api.github.com/repos/{OWNER}/{repo_name}/pages"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    data = {"source": {"branch": branch, "path": "/"}}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code in (201, 202):
        return resp.json().get("html_url")
    else:
        raise Exception(resp.text)
    log.info("enable pages ended")



def handle_round(task_id, round_number, generated_files):
    repo_name = f"task-{task_id}"

    # Round 1: Create new repo, enable Pages
    if round_number == 1:
        created = create_repo(repo_name)
        if not created:
            repo_name += "-new"
            create_repo(repo_name)
        pages_url = enable_pages(repo_name)
    
    # Commit all files
    sha_dict = {}
    for file in generated_files:
        path, content = file["path"], file["content"].encode("utf-8")
        sha = commit_file(repo_name, path, content, f"Round {round_number} commit")
        sha_dict[path] = sha

    return {"repo": repo_name, "commit_shas": sha_dict, "pages_url": pages_url if round_number==1 else None}



def push_to_github(task_id: str, round_number: int, base_dir: str = "generated_app") -> Dict[str, Any]:
    """
    Push the generated app to GitHub using handle_round API function.

    Args:
        task_id (str): Unique task ID from request JSON.
        round_number (int): Current round of generation.
        base_dir (str): Directory where app files are saved.

    Returns:
        Dict[str, Any]: Response from handle_round API with commit SHAs, repo name, and Pages URL.
    """

    # Step 1: Read all files from the generated app folder
    generated_files: List[Dict[str, str]] = []
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path, base_dir)  # relative to repo root
            with open(file_path, "rb") as file_obj:
                try:
                    content = file_obj.read().decode("utf-8")
                except UnicodeDecodeError:
                    # for binary files like images
                    import base64
                    content = base64.b64encode(file_obj.read()).decode("utf-8")
            generated_files.append({"path": rel_path, "content": content})

    # Step 2: Build dynamic repo name based on task ID
    repo_name = f"task-{task_id}"

    # Step 3: Call handle_round API
    try:
        response = handle_round(
            task_id=repo_name,
            round_number=round_number,
            generated_files=generated_files
        )
    except Exception as e:
        log.info(f"Error in handle_round API: {e}")
        response = {}

    return response
