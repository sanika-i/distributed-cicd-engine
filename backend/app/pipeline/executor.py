import subprocess
import os

from app.utils.git import clone_repo
from app.pipeline.parser import load_pipeline
from app.pipeline.store import (
    update_stage,
    add_log,
    complete_pipeline
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

        payload = {
            "pipeline_id": pipeline_id,
            "repo_path": repo_path,
            "pipeline": pipeline
        }

        send_job(payload)

        add_log(pipeline_id, "system", "INFO", "Pipeline sent to worker")

    except Exception as e:
        add_log(pipeline_id, "system", "ERROR", str(e))
        complete_pipeline(pipeline_id, "failed")