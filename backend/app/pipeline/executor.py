import subprocess

def run_commands(commands, cwd):
    results = []

    for cmd in commands:
        print(f"Running {cmd}")

        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )

        results.append({
            "command": cmd,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        })

        if result.returncode != 0:
            break
    
    return results

def run_pipeline_stages(pipeline, repo_path):
    stages = pipeline["stages"]
    jobs = pipeline["jobs"]

    execution_log = {}

    for stage in stages:
        for job_name, job in jobs.items():
            if job["stage"] == stage:
                result = run_commands(job["commands"], repo_path)
                execution_log[job_name] = result

    return execution_log

