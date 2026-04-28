from pathlib import Path
from git import Repo

def clone_repo(repo_url, branch, pipeline_id):
    base_dir = Path(__file__).resolve().parents[2]
    repos_dir = base_dir / "repos"

    repos_dir.mkdir(exist_ok=True)

    dest_path = repos_dir / pipeline_id

    if dest_path.exists():
        raise Exception(f"Repo already exists for pipeline {pipeline_id}")

    Repo.clone_from(repo_url, str(dest_path), branch=branch)

    return str(dest_path)