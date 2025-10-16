import os
import shutil
from app.logger import get_logger

log = get_logger(__name__)

def clear_generated_app_folder_except_git(folder_path, clear_git=False):
    """
    Deletes all files and subdirectories in a folder.
    Skips .git if clear_git is False.
    If clear_git is True, deletes everything including .git.
    """
    if not os.path.exists(folder_path):
        log.info(f"Folder not found: {folder_path}")
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        # Skip .git unless clear_git=True
        if item == ".git" and os.path.isdir(item_path) and not clear_git:
            continue

        # Delete files, links, or directories
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

    log.info(f"Cleared all files inside '{folder_path}'{' including .git' if clear_git else ' except .git (if present)'}")


def clear_generated_app_folder_by_round(folder_path, round_number):
    """
    Deletes all files and subdirectories in a folder.
    For round 1: clears everything including .git (fresh start).
    For round >1: clears all files except .git (preserve git history).
    """
    if not os.path.exists(folder_path):
        log.info(f"Folder not found: {folder_path}")
        return

    clear_git = round_number == 1  # clear .git only on round 1

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        # Skip .git unless we want to clear it
        if item == ".git" and os.path.isdir(item_path) and not clear_git:
            continue

        # Delete files, links, or directories
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

    log.info(f"Cleared all files inside '{folder_path}'{' including .git' if clear_git else ' except .git (if present)'}")