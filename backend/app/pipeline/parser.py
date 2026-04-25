import yaml
import os

def load_pipeline(repo_path):
    filepath = os.path.join(repo_path, "pipeline.yaml")

    if not os.path.exists(filepath):
        raise Exception("pipeline.yaml not found")
    
    with open(filepath, "r") as f:
        return yaml.safe_load(f)