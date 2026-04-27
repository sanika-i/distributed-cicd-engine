import yaml
import os

def validate_pipeline(pipeline):
    if "stages" not in pipeline:
        raise Exception("Missing 'stages'")

    if "jobs" not in pipeline:
        raise Exception("Missing 'jobs'")

    for job_name, job in pipeline["jobs"].items():
        if "stage" not in job:
            raise Exception(f"Job {job_name} missing 'stage'")
        if "commands" not in job:
            raise Exception(f"Job {job_name} missing 'commands'")

def load_pipeline(repo_path):
    filepath = os.path.join(repo_path, "pipeline.yaml")
    print("file path: ", filepath)

    if not os.path.exists(filepath):
        raise Exception("pipeline.yaml not found")
    
    with open(filepath, "r") as f:
        pipeline = yaml.safe_load(f)
    
    validate_pipeline(pipeline)
    return pipeline