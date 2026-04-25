from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PipelineRequest(BaseModel):
    repo_url: str
    branch: str = "main"

@app.get("/")
def read_root():
    return {"message" : "CI/CD system running"}