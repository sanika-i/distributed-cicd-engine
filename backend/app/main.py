from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.pipeline.store import (
    create_branch,
    create_pipeline,
    create_repo,
    delete_repo,
    get_branch,
    get_pipeline,
    get_repo,
    get_repo_by_url,
    init_db,
    get_db,
    list_repos,
    update_branch_pipeline
)
from app.pipeline.executor import execute_pipeline
from threading import Thread
from app.kafka.consumer import start_result_consumer
from dotenv import load_dotenv
from app.webhooks.provisioner import create_webhook, delete_webhook
from app.webhooks.github import verify_signature
import uuid

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    Thread(target=start_result_consumer, daemon=True).start()

class PipelineRequest(BaseModel):
    repo_url: str
    branch: str = "main"
class RepoRegistration(BaseModel):
    name: str
    repo_url: str
    branches: list[str]

def execute_pipeline(
    repo_url: str,
    branch: str = "main",
    commit_sha: str | None = None,
    repo_id: str | None = None,
    triggered_by: str = "manual"
):
    pipeline_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO pipelines
            (id, repo_url, status, repo_id, branch, commit_sha, triggered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pipeline_id,
                repo_url,
                "queued",
                repo_id,
                branch,
                commit_sha,
                triggered_by,
            ),
        )

    return pipeline_id

@app.get("/")
def read_root():
    return {"message" : "CI/CD system running"}

@app.post('/run_pipeline')
def run_pipeline(request: PipelineRequest):
    repo = get_repo_by_url(request.repo_url)

    pipeline_id = execute_pipeline(
        repo_url=request.repo_url,
        branch=request.branch,
        repo_id=repo['id'] if repo else None,
        triggered_by='manual'
    )

    if repo:
        update_branch_pipeline(repo['id'], request.branch, pipeline_id)

    return {
        'pipeline_id': pipeline_id,
        'status': 'queued'
    }

@app.get("/pipelines/{pipeline_id}")
def get_status(pipeline_id: str):
    return get_pipeline(pipeline_id)


@app.get("/pipelines/{pipeline_id}/logs")
def get_logs(pipeline_id: str):
    pipeline = get_pipeline(pipeline_id)
    return pipeline["logs"] if pipeline else []

@app.post('/repos')
def register_repo(payload: RepoRegistration):
    existing = get_repo_by_url(payload.repo_url)
    if existing:
        raise HTTPException(status_code=409, detail='Repository already registered')

    # webhook_id, webhook_secret = create_webhook(payload.repo_url)
    try:
        webhook_id, webhook_secret = create_webhook(payload.repo_url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Webhook creation failed: {str(e)}"
        )
    
    repo_id = str(uuid.uuid4())

    # create_repo({
    #     'id': repo_id,
    #     'name': payload.name,
    #     'repo_url': payload.repo_url,
    #     'webhook_id': str(webhook_id),
    #     'webhook_secret': webhook_secret
    # })

    try:
        create_repo({
            "id": repo_id,
            "name": payload.name,
            "repo_url": payload.repo_url,
            "webhook_id": str(webhook_id),
            "webhook_secret": webhook_secret
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    
    for branch in payload.branches:
        create_branch({
            'id': str(uuid.uuid4()),
            'repo_id': repo_id,
            'branch': branch.strip()
        })

    return get_repo(repo_id)


@app.get('/repos')
def get_repositories():
    return list_repos()

@app.get('/repos/{repo_id}')
def get_repository(repo_id: str):
    repo = get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail='Repository not found')
    return repo


@app.delete('/repos/{repo_id}')
def remove_repository(repo_id: str):
    repo = get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail='Repository not found')

    if repo.get('webhook_id'):
        delete_webhook(repo['repo_url'], repo['webhook_id'])

    delete_repo(repo_id)
    return {'message': 'Repository deleted successfully'}

@app.post('/webhooks/github')
async def github_webhook(request: Request):
    payload = await request.body()
    data = await request.json()

    repo_url = data['repository']['clone_url']
    branch = data['ref'].split('/')[-1]
    commit_sha = data['after']

    repo = get_repo_by_url(repo_url)
    if not repo:
        return {'status': 'ignored', 'reason': 'repo not registered'}

    signature = request.headers.get('X-Hub-Signature-256')
    verify_signature(payload, signature, repo['webhook_secret'])

    registered_branch = get_branch(repo['id'], branch)
    if not registered_branch:
        return {'status': 'ignored', 'reason': 'branch not registered'}

    pipeline_id = execute_pipeline(
        repo_url=repo_url,
        branch=branch,
        commit_sha=commit_sha,
        repo_id=repo['id'],
        triggered_by='webhook'
    )

    update_branch_pipeline(repo['id'], branch, pipeline_id)

    return {
        'status': 'triggered',
        'pipeline_id': pipeline_id
    }