import os
import shutil

def clear_generated_app_folder_except_git(folder_path):
    """
    Deletes all files and subdirectories in a folder
    except the `.git` directory (if present).
    If `.git` is not present, clears everything.
    """
    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        # Skip .git directory (if exists)
        if item == ".git" and os.path.isdir(item_path):
            continue

        # Delete files, links, or directories
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

    print(f"✅ Cleared all files and subdirectories inside '{folder_path}' except .git (if present).")