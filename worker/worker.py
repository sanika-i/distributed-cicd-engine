import subprocess
import json
import os
import socket
import tempfile
import shutil
from git import Repo
from kafka import KafkaConsumer, KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
WORKER_ID = f"{socket.gethostname()}-{os.getpid()}"

print(f"Worker starting... id={WORKER_ID}")


def _get_consumer():
    return KafkaConsumer(
        "jobs",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="worker-group"
    )


def _get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )


def clone_at_commit(repo_url, branch, commit_sha):
    tmpdir = tempfile.mkdtemp(prefix=f"cicd-{commit_sha[:7]}-")
    print(f"  Cloning {repo_url}@{commit_sha[:7]} into {tmpdir}")
    repo = Repo.clone_from(repo_url, tmpdir, branch=branch)
    repo.git.checkout(commit_sha)
    return tmpdir


def run_command(cmd, repo_path):
    """
    Run command directly in the repo directory.
    No Docker needed — the worker container is already isolated.
    """
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=repo_path
    )
    return result


def execute_stage(stage, jobs, repo_path):
    stage_logs = []
    success = True

    for job_name, job in jobs.items():
        for cmd in job["commands"]:
            print(f"  [{stage}] running: {cmd}")
            result = run_command(cmd, repo_path)

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
    repo_url    = data["repo_url"]
    branch      = data["branch"]
    commit_sha  = data["commit_sha"]
    stage       = data["stage"]
    jobs        = data["jobs"]

    print(f"[{WORKER_ID}] picked up stage='{stage}'  pipeline={pipeline_id}")

    repo_path = None
    try:
        repo_path = clone_at_commit(repo_url, branch, commit_sha)
        success, logs = execute_stage(stage, jobs, repo_path)
    except Exception as e:
        print(f"[{WORKER_ID}] error: {e}")
        success = False
        logs = [{"stdout": "", "stderr": str(e), "success": False}]
    finally:
        if repo_path and os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
            print(f"  Cleaned up {repo_path}")

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