from fastapi import FastAPI
from pydantic import BaseModel
from app.utils.git import clone_repo
from app.pipeline.parser import load_pipeline
from app.pipeline.executor import run_pipeline_stages

app = FastAPI()

class PipelineRequest(BaseModel):
    repo_url: str
    branch: str = "main"

@app.get("/")
def read_root():
    return {"message" : "CI/CD system running"}

@app.post("/run_pipeline")
def run_pipeline(req: PipelineRequest):

    repo_path = clone_repo(req.repo_url, req.branch)

    pipeline = load_pipeline(repo_path)

    result = run_pipeline_stages(pipeline, repo_path)

    return {
        "result": result
    }
