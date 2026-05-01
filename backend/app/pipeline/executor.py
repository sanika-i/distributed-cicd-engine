from app.utils.git import resolve_commit_sha, load_pipeline_from_url
from app.pipeline.store import (
    update_stage,
    add_log,
    complete_pipeline, 
    save_pipeline_state
)
from app.kafka.producer import send_job

def execute_pipeline(pipeline_id, repo_url, branch, commit_sha=None):
    try:
        add_log(pipeline_id, "system", "INFO", "Pipeline started")
        if not commit_sha:
            # Manual trigger via /run_pipeline — resolve from GitHub API
            add_log(pipeline_id, "system", "INFO", f"Resolving HEAD for branch: {branch}")
            try:
                commit_sha = resolve_commit_sha(repo_url, branch)
                add_log(pipeline_id, "system", "INFO", f"Commit: {commit_sha}")
            except Exception as e:
                add_log(pipeline_id, "system", "ERROR", f"Failed to resolve commit: {e}")
                complete_pipeline(pipeline_id, "failed")
                return
        else:
            # Webhook trigger — SHA already known
            add_log(pipeline_id, "system", "INFO", f"Commit: {commit_sha} (from webhook)")
 
        add_log(pipeline_id, "system", "INFO", "Fetching pipeline.yaml")
        try:
            pipeline = load_pipeline_from_url(repo_url, branch)
        except Exception as e:
            add_log(pipeline_id, "system", "ERROR", f"Failed to load pipeline.yaml: {e}")
            complete_pipeline(pipeline_id, "failed")
            return

        stages = pipeline["stages"]

        for stage in stages:
            update_stage(pipeline_id, stage, "pending")

        first_stage = stages[0]
        remaining = stages[1:]

        save_pipeline_state(
            pipeline_id,
            repo_url=repo_url,
            branch=branch,
            commit_sha=commit_sha,
            remaining_stages=remaining,
            pipeline_def=pipeline
        )

        _dispatch_stage(pipeline_id, repo_url, branch, commit_sha, pipeline, first_stage)

        add_log(pipeline_id, "system", "INFO", f"Dispatched stage: {first_stage}")

    except Exception as e:
        add_log(pipeline_id, "system", "ERROR", str(e))
        complete_pipeline(pipeline_id, "failed")

def _dispatch_stage(pipeline_id, repo_url, branch, commit_sha, pipeline, stage):
    """Build the single-stage job payload and send it to Kafka."""
    jobs_for_stage = {
        name: job
        for name, job in pipeline["jobs"].items()
        if job["stage"] == stage
    }
 
    payload = {
        "pipeline_id": pipeline_id,
        "repo_url":    repo_url, 
        "branch":      branch,
        "commit_sha":  commit_sha,
        "stage":       stage,
        "jobs":        jobs_for_stage
    }
 
    update_stage(pipeline_id, stage, "running")
    send_job(payload)