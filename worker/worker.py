import subprocess
import json
import os
from kafka import KafkaConsumer, KafkaProducer

print("Worker starting...")

consumer = KafkaConsumer(
    "jobs",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="worker-group"
)

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("Worker ready\n")


def run_docker_command(cmd, image, repo_path):
    repo_path = os.path.abspath(repo_path)

    docker_cmd = (
        f'docker run --rm '
        f'-v {repo_path}:/app '
        f'-w /app '
        f'{image} sh -c "{cmd}"'
    )

    result = subprocess.run(
        docker_cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    return result


for message in consumer:
    print("Pipeline received")

    data = message.value

    pipeline_id = data["pipeline_id"]
    repo_path = data["repo_path"]
    pipeline = data["pipeline"]

    stages = pipeline["stages"]
    jobs = pipeline["jobs"]

    stage_results = []

    for stage in stages:
        print(f"Running stage: {stage}")

        stage_logs = []
        success = True

        for job_name, job in jobs.items():
            if job["stage"] != stage:
                continue

            image = job.get("image", "ubuntu")

            for cmd in job["commands"]:
                result = run_docker_command(cmd, image, repo_path)

                stage_logs.append({
                    "stage": stage,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0
                })

                if result.returncode != 0:
                    success = False
                    break

            if not success:
                break

        stage_results.append({
            "stage": stage,
            "success": success,
            "logs": stage_logs
        })

        if not success:
            break

    result_payload = {
        "pipeline_id": pipeline_id,
        "stages": stage_results
    }

    producer.send("results", result_payload)
    producer.flush()

    print("Pipeline execution finished\n")