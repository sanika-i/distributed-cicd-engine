from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.pipeline.store import (
    create_pipeline,
    get_pipeline,
    init_db,
    recover_interrupted_pipelines
)
from app.pipeline.executor import execute_pipeline
from threading import Thread, Event
from app.kafka.consumer import start_result_consumer

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/pipelines/{pipeline_id}")
def get_status(pipeline_id: str):
    return get_pipeline(pipeline_id)


@app.get("/pipelines/{pipeline_id}/logs")
def get_logs(pipeline_id: str):
    pipeline = get_pipeline(pipeline_id)
    return pipeline["logs"] if pipeline else []
