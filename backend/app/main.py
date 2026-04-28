from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from app.pipeline.store import (
    create_pipeline,
    get_pipeline,
    init_db
)
from app.pipeline.executor import execute_pipeline
from threading import Thread
from app.kafka.consumer import start_result_consumer

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()
    Thread(target=start_result_consumer, daemon=True).start()

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
