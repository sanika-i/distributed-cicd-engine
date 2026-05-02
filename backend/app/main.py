from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.pipeline.store import (
    create_pipeline,
    get_pipeline,
    init_db,
    recover_interrupted_pipelines,
    list_pipelines
)
from app.pipeline.executor import execute_pipeline
from threading import Thread, Event
from app.kafka.consumer import start_result_consumer
import hmac
import hashlib
import os

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

consumer_ready = Event()

@app.on_event("startup")
def startup():
    init_db()
    recover_interrupted_pipelines()
    Thread(target=start_result_consumer, args=(consumer_ready,), daemon=True).start()
    consumer_ready.wait(timeout=30)
    print("Consumer ready — accepting requests")

class PipelineRequest(BaseModel):
    repo_url: str
    branch: str = "main"

@app.get("/")
def read_root():
    return {"message" : "CI/CD system running"}

@app.post("/run_pipeline")
def run_pipeline(req: PipelineRequest, background_tasks: BackgroundTasks):

    pipeline_id = create_pipeline()

    background_tasks.add_task(
        execute_pipeline,
        pipeline_id,
        req.repo_url,
        req.branch
    )

    return {
        "pipeline_id": pipeline_id,
        "status": "started"
    }

@app.get("/pipelines")
def get_all_pipelines():
    return list_pipelines()

@app.get("/pipelines/{pipeline_id}")
def get_status(pipeline_id: str):
    return get_pipeline(pipeline_id)


@app.get("/pipelines/{pipeline_id}/logs")
def get_logs(pipeline_id: str):
    pipeline = get_pipeline(pipeline_id)
    return pipeline["logs"] if pipeline else []

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    # ── 1. Read raw body ────────────────────────────────────────────────
    # We need the raw bytes to verify the signature — once parsed as JSON
    # the byte-for-byte content may differ, breaking the HMAC check
    body = await request.body()

    # ── 2. Validate HMAC signature ──────────────────────────────────────
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing signature header")

    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    # Use hmac.compare_digest to prevent timing attacks
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # ── 3. Only handle push events ──────────────────────────────────────
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "ping":
        # GitHub sends a ping when the webhook is first configured
        return {"message": "pong"}

    if event_type != "push":
        # Ignore pull_request, issues, etc.
        return {"message": f"Ignoring event: {event_type}"}

    # ── 4. Parse payload ────────────────────────────────────────────────
    payload = await request.json()

    # Extract branch name from ref (e.g. "refs/heads/main" → "main")
    ref = payload.get("ref", "")
    if not ref.startswith("refs/heads/"):
        return {"message": "Not a branch push, ignoring"}

    branch = ref.replace("refs/heads/", "")

    # Extract repo URL
    repo_url = payload["repository"]["clone_url"]

    repo_name = payload["repository"]["name"]

    commit_message = payload.get("head_commit", {}).get("message", "")

    # Extract commit SHA — GitHub gives us this directly so we don't
    # need to call the GitHub API to resolve it
    commit_sha = payload["after"]

    # Ignore pushes that delete a branch
    if commit_sha == "0000000000000000000000000000000000000000":
        return {"message": "Branch deletion, ignoring"}

    # ── 5. Trigger pipeline ─────────────────────────────────────────────
    pipeline_id = create_pipeline(
    repo_name,
    branch,
    commit_message
    )
    background_tasks.add_task(
        execute_pipeline,
        pipeline_id,
        repo_url,
        branch,
        commit_sha   # pass directly — no need to resolve via API
    )

    print(f"[webhook] Pipeline {pipeline_id} triggered for {repo_url}@{branch} ({commit_sha[:7]})")

    return {
        "pipeline_id": pipeline_id,
        "repo": repo_url,
        "branch": branch,
        "commit": commit_sha[:7],
        "status": "triggered"
    }
