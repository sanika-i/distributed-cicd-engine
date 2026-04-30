import yaml
import requests
from git import Repo
import tempfile
import os


def resolve_commit_sha(repo_url, branch):
    """
    Returns the latest commit SHA on a branch without doing a full clone.
    Uses the GitHub API for github.com URLs, falls back to ls-remote otherwise.
    """
    if "github.com" in repo_url:
        parts = repo_url.rstrip("/").rstrip(".git").split("github.com/")[-1].split("/")
        owner, repo = parts[0], parts[1]

        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()
        return resp.json()["sha"]
    else:
        import subprocess
        result = subprocess.run(
            ["git", "ls-remote", repo_url, f"refs/heads/{branch}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"git ls-remote failed: {result.stderr}")
        line = result.stdout.strip()
        if not line:
            raise Exception(f"Branch '{branch}' not found in {repo_url}")
        return line.split()[0]


def load_pipeline_from_url(repo_url, branch):
    """
    Fetches and parses pipeline.yaml from a GitHub repo without a full clone.
    Falls back to a shallow clone for non-GitHub hosts.
    """
    if "github.com" in repo_url:
        parts = repo_url.rstrip("/").rstrip(".git").split("github.com/")[-1].split("/")
        owner, repo = parts[0], parts[1]

        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/pipeline.yaml"
        resp = requests.get(raw_url, timeout=10)

        if resp.status_code == 404:
            raise Exception("pipeline.yaml not found in repository root")
        resp.raise_for_status()

        pipeline = yaml.safe_load(resp.text)
        _validate_pipeline(pipeline)
        return pipeline
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            Repo.clone_from(repo_url, tmpdir, branch=branch, depth=1)
            filepath = os.path.join(tmpdir, "pipeline.yaml")
            if not os.path.exists(filepath):
                raise Exception("pipeline.yaml not found in repository root")
            with open(filepath) as f:
                pipeline = yaml.safe_load(f)
            _validate_pipeline(pipeline)
            return pipeline


def _validate_pipeline(pipeline):
    if "stages" not in pipeline:
        raise Exception("pipeline.yaml missing 'stages'")
    if "jobs" not in pipeline:
        raise Exception("pipeline.yaml missing 'jobs'")
    for job_name, job in pipeline["jobs"].items():
        if "stage" not in job:
            raise Exception(f"Job '{job_name}' missing 'stage'")
        if "commands" not in job:
            raise Exception(f"Job '{job_name}' missing 'commands'")