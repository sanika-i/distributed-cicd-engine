import subprocess
import json
import os
import socket
from kafka import KafkaConsumer, KafkaProducer

WORKER_ID = f"{socket.gethostname()}-{os.getpid()}"

print(f"Worker starting... id={WORKER_ID}")


def _get_consumer():
    return KafkaConsumer(
        "jobs",
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="worker-group"
    )


def _get_producer():
    return KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )


def run_docker_command(cmd, image, repo_path):
    repo_path = os.path.abspath(repo_path)
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{repo_path}:/app",
        "-w", "/app",
        image,
        "sh", "-c", cmd 
    ]
    result = subprocess.run(
        docker_cmd,
        shell=False,
        capture_output=True,
        text=True
    )
    return result


def execute_stage(pipeline_id, stage, jobs, repo_path):
    """
    Run all jobs that belong to this stage.
    Returns (success: bool, logs: list[dict])
    """
    stage_logs = []
    success = True

    for job_name, job in jobs.items():
        image = job.get("image", "ubuntu")

        for cmd in job["commands"]:
            print(f"  [{stage}] running: {cmd}")
            result = run_docker_command(cmd, image, repo_path)

            stage_logs.append({
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "success": result.returncode == 0
            })

            if result.returncode != 0:
                print(f"  [{stage}] command failed (exit {result.returncode})")
                success = False
                break 

        if not success:
            break

    return success, stage_logs


consumer = _get_consumer()
producer = _get_producer()
print(f"Worker ready  id={WORKER_ID}\n")

for message in consumer:
    data = message.value

    pipeline_id = data["pipeline_id"]
    repo_path   = data["repo_path"]
    stage       = data["stage"]
    jobs        = data["jobs"]

    print(f"[{WORKER_ID}] picked up stage='{stage}'  pipeline={pipeline_id}")

    success, logs = execute_stage(pipeline_id, stage, jobs, repo_path)

    result_payload = {
        "pipeline_id": pipeline_id,
        "stage":       stage,
        "success":     success,
        "logs":        logs,
        "worker_id":   WORKER_ID
    }

    producer.send("results", result_payload)
    producer.flush()

    status = "success" if success else "failed"
    print(f"[{WORKER_ID}] stage='{stage}' finished → {status}\n")