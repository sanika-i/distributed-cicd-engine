from kafka import KafkaConsumer
import json

from app.pipeline.store import (
    update_stage,
    add_log,
    complete_pipeline
)

consumer = KafkaConsumer(
    "results",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="backend-group"
)


def start_result_consumer():
    print("Result consumer started")

    for message in consumer:
        result = message.value

        pipeline_id = result["pipeline_id"]
        stages = result["stages"]

        pipeline_success = True

        for stage_data in stages:
            stage = stage_data["stage"]
            success = stage_data["success"]

            if success:
                update_stage(pipeline_id, stage, "success")
            else:
                update_stage(pipeline_id, stage, "failed")
                pipeline_success = False

            for log in stage_data["logs"]:
                if log["stdout"]:
                    add_log(pipeline_id, stage, "STDOUT", log["stdout"])
                if log["stderr"]:
                    add_log(pipeline_id, stage, "STDERR", log["stderr"])

        if pipeline_success:
            complete_pipeline(pipeline_id, "success")
            add_log(pipeline_id, "system", "INFO", "Pipeline completed successfully")
        else:
            complete_pipeline(pipeline_id, "failed")
            add_log(pipeline_id, "system", "INFO", "Pipeline failed")