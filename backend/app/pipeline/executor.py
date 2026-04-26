import subprocess

from app.utils.git import clone_repo
from app.pipeline.parser import load_pipeline
from app.pipeline.store import (
    update_stage,
    add_log,
    complete_pipeline
)


def execute_pipeline(pipeline_id, repo_url, branch):
    try:
        repo_path = clone_repo(repo_url, branch)
        pipeline = load_pipeline(repo_path)

        stages = pipeline["stages"]
        jobs = pipeline["jobs"]

        for stage in stages:
            update_stage(pipeline_id, stage, "pending")

        for stage in stages:
            update_stage(pipeline_id, stage, "running")

            for job_name, job in jobs.items():
                if job["stage"] == stage:
                    for cmd in job["commands"]:
                        add_log(pipeline_id, f"[{stage}] Running: {cmd}")

                        result = subprocess.run(
                            cmd,
                            shell=True,
                            cwd=repo_path,
                            capture_output=True,
                            text=True
                        )

                        add_log(pipeline_id, result.stdout)
                        add_log(pipeline_id, result.stderr)

                        if result.returncode != 0:
                            add_log(pipeline_id, f"[{stage}] FAILED")
                            update_stage(pipeline_id, stage, "failed")
                            complete_pipeline(pipeline_id, "failed")
                            return

            update_stage(pipeline_id, stage, "success")

        complete_pipeline(pipeline_id, "success")

    except Exception as e:
        add_log(pipeline_id, str(e))
        complete_pipeline(pipeline_id, "failed")