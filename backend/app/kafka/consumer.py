from kafka import KafkaConsumer
import json
from app.kafka.producer import send_job
from app.pipeline.store import (
    update_stage,
    add_log,
    complete_pipeline,
    get_pipeline_state,
    update_pipeline_state
)

def _get_consumer():
    return KafkaConsumer(
        "results",
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="backend-group"
    )

def start_result_consumer():
    print("Result consumer started")

    consumer = _get_consumer()

    for message in consumer:
        result = message.value

        pipeline_id = result["pipeline_id"]
        stage = result["stage"]
        success = result["success"]
        logs = result["logs"]

        for log in logs:
            if log.get("stdout"):
                for line in log["stdout"].splitlines():
                    line = line.strip()
                    if line:
                        add_log(pipeline_id, stage, "STDOUT", line)
            if log.get("stderr"):
                for line in log["stderr"].splitlines():
                    line = line.strip()
                    if line:
                        add_log(pipeline_id, stage, "STDERR", line)

        if success:
            update_stage(pipeline_id, stage, "success")
            add_log(pipeline_id, "system", "INFO", f"Stage '{stage}' succeeded")
        else:
            update_stage(pipeline_id, stage, "failed")
            add_log(pipeline_id, "system", "INFO", f"Stage '{stage}' failed")
            complete_pipeline(pipeline_id, "failed")
            print(f"[scheduler] Pipeline {pipeline_id} failed at stage '{stage}'")
            continue

        state = get_pipeline_state(pipeline_id)
        if state is None:
            print(f"[scheduler] No state found for pipeline {pipeline_id}")
            continue

        remaining = state["remaining_stages"]

        if not remaining:
            complete_pipeline(pipeline_id, "success")
            add_log(pipeline_id, "system", "INFO", "Pipeline completed successfully")
            print(f"[scheduler] Pipeline {pipeline_id} completed successfully")
        else:
            next_stage = remaining[0]
            new_remaining = remaining[1:]
 
            update_pipeline_state(pipeline_id, new_remaining)
 
            jobs_for_stage = {
                name: job
                for name, job in state["pipeline_def"]["jobs"].items()
                if job["stage"] == next_stage
            }
 
            payload = {
                "pipeline_id": pipeline_id,
                "repo_path": state["repo_path"],
                "stage": next_stage,
                "jobs": jobs_for_stage
            }
 
            update_stage(pipeline_id, next_stage, "running")
            send_job(payload)
            add_log(pipeline_id, "system", "INFO", f"Dispatched stage: {next_stage}")
            print(f"[scheduler] Pipeline {pipeline_id} → dispatched stage '{next_stage}'")