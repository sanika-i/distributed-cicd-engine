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
        update_stage(pipeline_id, "clone", "running")
        add_log(pipeline_id, "clone", "INFO", f"Cloning repo: {repo_url} (branch: {branch})")

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
        jobs = pipeline["jobs"]

        # Initialize stages
        for stage in stages:
            update_stage(pipeline_id, stage, "pending")

        for stage in stages:
            update_stage(pipeline_id, stage, "running")

            for job_name, job in jobs.items():
                if job["stage"] == stage:
                    for cmd in job["commands"]:
                        add_log(pipeline_id, stage, "INFO", f"Running: {cmd}")

                        result = subprocess.run(
                            cmd,
                            shell=True,
                            cwd=repo_path,
                            capture_output=True,
                            text=True
                        )

                        # Log stdout line by line
                        for line in result.stdout.splitlines():
                            add_log(pipeline_id, stage, "STDOUT", line)

                        # Log stderr line by line
                        for line in result.stderr.splitlines():
                            add_log(pipeline_id, stage, "STDERR", line)

                        if result.returncode != 0:
                            add_log(pipeline_id, stage, "ERROR", "Command failed")
                            update_stage(pipeline_id, stage, "failed")
                            complete_pipeline(pipeline_id, "failed")
                            return

            update_stage(pipeline_id, stage, "success")

        complete_pipeline(pipeline_id, "success")

    except Exception as e:
        add_log(pipeline_id, "system", "ERROR", str(e))
        complete_pipeline(pipeline_id, "failed")