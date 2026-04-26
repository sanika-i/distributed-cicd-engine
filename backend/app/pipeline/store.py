import uuid

pipelines = {}

def create_pipeline():
    pipeline_id = str(uuid.uuid4())

    pipelines[pipeline_id] = {
        "status": "running",
        "stages": {},
        "logs": []
    }

    return pipeline_id

def update_stage(pipeline_id, stage, status):
    pipelines[pipeline_id]["stages"][stage] = status

def add_log(pipeline_id, log):
    pipelines[pipeline_id]["logs"].append(log)

def complete_pipeline(pipeline_id, status):
    pipelines[pipeline_id]["status"] = status

def get_pipeline(pipeline_id):
    return pipelines.get(pipeline_id)