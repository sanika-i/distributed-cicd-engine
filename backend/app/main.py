from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.pipeline.store import (
    create_pipeline,
    get_pipeline,
    init_db
)
from fastapi import BackgroundTasks
from app.pipeline.executor import execute_pipeline

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

@app.get("/pipelines/{pipeline_id}")
def get_status(pipeline_id: str):
    return get_pipeline(pipeline_id)


@app.get("/pipelines/{pipeline_id}/logs")
def get_logs(pipeline_id: str):
    pipeline = get_pipeline(pipeline_id)
    return pipeline["logs"] if pipeline else []
