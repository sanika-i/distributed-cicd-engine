import secrets
import httpx
import os

GITHUB_API = "https://api.github.com"


def parse_github_repo(repo_url: str):
    parts = repo_url.rstrip('/').replace('.git', '').split('/')
    return parts[-2], parts[-1]


def create_webhook(repo_url: str):
    owner, repo = parse_github_repo(repo_url)
    secret = secrets.token_hex(32)

    payload = {
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "url": f"{os.getenv('WEBHOOK_BASE_URL')}/webhooks/github",
            "content_type": "json",
            "secret": secret,
            "insecure_ssl": "0"
        }
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json"
    }

    response = httpx.post(
        f"{GITHUB_API}/repos/{owner}/{repo}/hooks",
        json=payload,
        headers=headers,
        timeout=30.0
    )
    response.raise_for_status()

    return response.json()["id"], secret


def delete_webhook(repo_url: str, webhook_id: str):
    owner, repo = parse_github_repo(repo_url)
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json"
    }

    response = httpx.delete(
        f"{GITHUB_API}/repos/{owner}/{repo}/hooks/{webhook_id}",
        headers=headers,
        timeout=30.0
    )
    response.raise_for_status()
    