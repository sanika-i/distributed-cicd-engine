import os
import shutil
from git import Repo

def clone_repo(repo_url, branch, dest="repos"):
    if os.path.exists(dest):
        shutil.rmtree(dest)

    Repo.clone_from(repo_url, dest, branch = branch)

    return dest