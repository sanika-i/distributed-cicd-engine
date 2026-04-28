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

# def run_docker_command(cmd, image, repo_path, pipeline_id, stage):
#     repo_path = os.path.abspath(repo_path)

#     docker_cmd = (
#         f'docker run --rm '
#         f'-v {repo_path}:/app '
#         f'-w /app '
#         f'{image} sh -c "{cmd}"'
#     )

#     add_log(pipeline_id, stage, "INFO", f"Docker: {docker_cmd}")

#     result = subprocess.run(
#         docker_cmd,
#         shell=True,
#         capture_output=True,
#         text=True
#     )

#     return result


def execute_pipeline(pipeline_id, repo_url, branch):
    try:
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
        jobs = pipeline["jobs"]


        for stage in stages:
            update_stage(pipeline_id, stage, "pending")

        for stage in stages:
            update_stage(pipeline_id, stage, "queued")

            for job_name, job in jobs.items():
                if job["stage"] != stage:
                    continue

                job_payload = {
                    "pipeline_id": pipeline_id,
                    "stage": stage,
                    "job_name": job_name,
                    "repo_path": repo_path,
                    "commands": job["commands"],
                    "image": job.get("image", "ubuntu")
                }

                send_job(job_payload)

                add_log(pipeline_id, stage, "INFO", f"Job sent to queue: {job_name}")

                # image = job.get("image", "ubuntu")

                # add_log(pipeline_id, stage, "INFO", f"Starting job: {job_name} (image={image})")

        #         for cmd in job["commands"]:
        #             add_log(pipeline_id, stage, "INFO", f"Running: {cmd}")

        #             result = run_docker_command(
        #                 cmd,
        #                 image,
        #                 repo_path,
        #                 pipeline_id,
        #                 stage
        #             )

        #             for line in result.stdout.splitlines():
        #                 add_log(pipeline_id, stage, "STDOUT", line)

        #             for line in result.stderr.splitlines():
        #                 add_log(pipeline_id, stage, "STDERR", line)

        #             if result.returncode != 0:
        #                 add_log(pipeline_id, stage, "ERROR", "Command failed")
        #                 update_stage(pipeline_id, stage, "failed")
        #                 complete_pipeline(pipeline_id, "failed")
        #                 return

        #         add_log(pipeline_id, stage, "INFO", f"Job completed: {job_name}")

        #     update_stage(pipeline_id, stage, "success")

        # complete_pipeline(pipeline_id, "success")

    except Exception as e:
        add_log(pipeline_id, "system", "ERROR", str(e))
        complete_pipeline(pipeline_id, "failed")