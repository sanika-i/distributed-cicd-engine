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
    for message in consumer:
        result = message.value

        pipeline_id = result["pipeline_id"]
        stage = result["stage"]

        if result["success"]:
            update_stage(pipeline_id, stage, "success")
        else:
            update_stage(pipeline_id, stage, "failed")
            complete_pipeline(pipeline_id, "failed")

        for log in result["logs"]:
            if log["stdout"]:
                add_log(pipeline_id, stage, "STDOUT", log["stdout"])
            if log["stderr"]:
                add_log(pipeline_id, stage, "STDERR", log["stderr"])