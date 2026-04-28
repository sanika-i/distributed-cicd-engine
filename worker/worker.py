import subprocess
import json
import os
from kafka import KafkaConsumer, KafkaProducer

print("Starting worker...")

consumer = KafkaConsumer(
    "jobs",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="worker-group",
    enable_auto_commit=True
)

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("Worker connected to Kafka. Waiting for jobs...\n")

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

    try:
        job = message.value

        pipeline_id = job["pipeline_id"]
        stage = job["stage"]
        commands = job["commands"]
        image = job["image"]
        repo_path = job["repo_path"]

        logs = []
        success = True

        for cmd in commands:
            print(f"\n Executing command: {cmd}")

            result = run_docker_command(cmd, image, repo_path)

            logs.append({
                "cmd": cmd,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            })

            if result.returncode != 0:
                print("Command failed!")
                success = False
                break

        result_payload = {
            "pipeline_id": pipeline_id,
            "stage": stage,
            "success": success,
            "logs": logs
        }

        print("\nSending result back to Kafka:")
        print(result_payload)

        producer.send("results", result_payload)
        producer.flush()

        print(" Result sent successfully!\n")

    except Exception as e:
        print("ERROR in worker:")
        print(str(e))