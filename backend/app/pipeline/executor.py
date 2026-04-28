import subprocess
import os

from app.utils.git import clone_repo
from app.pipeline.parser import load_pipeline
from app.pipeline.store import (
    update_stage,
    add_log,
    complete_pipeline, 
    save_pipeline_state
)
from app.kafka.producer import send_job

def execute_pipeline(pipeline_id, repo_url, branch):
    try:
        add_log(pipeline_id, "system", "INFO", "Pipeline started")
        update_stage(pipeline_id, "clone", "running")
        add_log(pipeline_id, "clone", "INFO", f"Cloning repo: {repo_url}")

        try:
            repo_path = clone_repo(repo_url, branch, pipeline_id)
            add_log(pipeline_id, "clone", "INFO", "Clone successful")
            update_stage(pipeline_id, "clone", "success")
        except Exception as e:
            add_log(pipeline_id, "clone", "ERROR", str(e))
            update_stage(pipeline_id, "clone", "failed")
            complete_pipeline(pipeline_id, "failed")
            return

        pipeline = load_pipeline(repo_path)

        stages = pipeline["stages"]

        for stage in stages:
            update_stage(pipeline_id, stage, "pending")

        first_stage = stages[0]
        remaining = stages[1:]

        save_pipeline_state(pipeline_id, repo_path, remaining, pipeline)

        _dispatch_stage(pipeline_id, repo_path, pipeline, first_stage)

        add_log(pipeline_id, "system", "INFO", f"Dispatched stage: {first_stage}")

    except Exception as e:
        add_log(pipeline_id, "system", "ERROR", str(e))
        complete_pipeline(pipeline_id, "failed")

def _dispatch_stage(pipeline_id, repo_path, pipeline, stage):
    """Build the single-stage job payload and send it to Kafka."""
    jobs_for_stage = {
        name: job
        for name, job in pipeline["jobs"].items()
        if job["stage"] == stage
    }
 
    payload = {
        "pipeline_id": pipeline_id,
        "repo_path": repo_path,
        "stage": stage,
        "jobs": jobs_for_stage
    }
 
    update_stage(pipeline_id, stage, "running")
    send_job(payload)