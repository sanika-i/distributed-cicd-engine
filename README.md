# Distributed CI/CD Pipeline System (Mini Jenkins)

## Team Members
1. Aishwarya Kore
2. Sanika Indorkar

## 1. Project Overview
This project is a distributed CI/CD pipeline system inspired by tools like Jenkins. It is designed to automate the process of building, testing, and executing pipelines across multiple worker nodes in a scalable and distributed manner.

The system leverages message queues, containerization, and distributed workers to efficiently execute jobs in parallel, improving performance and scalability.

---

## 2. Project Description

The system works by connecting a GitHub repository to this CI/CD system via a webhook.

### Workflow:

1. User adds the backend endpoint as a webhook in their GitHub repository.
2. On every push event, GitHub sends a webhook payload to the backend.
3. The backend extracts repository details (repo URL, branch).
4. It resolves the latest commit SHA and fetches the pipeline configuration.
5. The pipeline is broken into stages and pushed to Kafka.
6. Worker nodes consume and execute stages in a distributed manner.
7. Results and logs are sent back and stored.
8. Pipeline status is updated and can be monitored.

This design removes manual triggering and enables fully automated CI/CD workflows.

---

## 3. Tech Stack

### Backend
- Python
- FastAPI
- SQLite

### Frontend
- Vue3 + vite

### Messaging Queue
- Apache Kafka

### Workers
- Python-based distributed workers
- Kafka consumers

### Containerization
- Docker

### Orchestration
- Kubernetes + KEDA (auto-scaling)

### Configuration
- YAML-based pipelines

---

## 4. System Architecture

- Backend acts as:
  - Webhook listener
  - Scheduler
  - State manager

- Kafka handles:
  - Job distribution (`jobs` topic)
  - Result collection (`results` topic)

- Workers:
  - Execute pipeline stages
  - Run tasks in isolated environments

- Database:
  - Stores pipeline metadata, logs, and state

---

## 5. Key Features

### 5.1 GitHub Webhook Integration
- Automatic pipeline triggering on `push` events
- No manual API calls required

### 5.2 Distributed Stage Execution
- Pipelines split into stages
- Each stage assigned to workers
- Execution depends on previous stage completion :contentReference[oaicite:0]{index=0}

### 5.3 True Distributed Workers
- Workers independently clone repositories
- Each worker checks out the exact commit SHA
- Ensures consistency across all stages :contentReference[oaicite:1]{index=1}

### 5.4 Kafka-Based Communication
- Decoupled architecture using message queues
- Scalable job distribution

### 5.5 Containerized Execution
- Jobs run in isolated environments (Docker locally)
- Native execution inside Kubernetes pods

### 5.6 Pipeline State Management
- Tracks:
  - Running pipelines
  - Stage-level progress
  - Failures and logs

### 5.7 Auto-Scaling Workers
- KEDA scales workers based on Kafka lag
- Dynamic scaling depending on system load :contentReference[oaicite:2]{index=2}

### 5.8 Persistent Storage
- SQLite database stored in `/data/cicd.db`
- Data persists across restarts

---

## 7. How to Run

### 7.1 Using Docker Compose (Recommended)

```bash
docker-compose up --build
```

This will start:
- Kafka + Zookeeper
- Backend
- Worker nodes

### 7.2 Trigger via GitHub Webhook

1. Go to your GitHub repository
2. Navigate to: **Settings → Webhooks → Add Webhook**
3. Add:
   - **Payload URL:** `http://<your-backend-url>/webhook`
   - **Content type:** `application/json`
   - **Event:** Push

Now every push will automatically trigger a pipeline.

### 7.3 Manual Trigger (Optional)

```bash
curl -X POST http://127.0.0.1:<PORT>/run_pipeline \
  -H "Content-Type: application/json" \
  -d '{
        "repo_url": "<repo-url>",
        "branch": "main"
      }'
```

---

## 8. Kubernetes Deployment (Advanced)

**Steps:**

1. Start Minikube:
```bash
   minikube start
```

2. Build images inside Minikube:
```bash
   eval $(minikube docker-env)
   docker build -t cicd-backend:latest ./backend
   docker build -t cicd-worker:latest ./worker
```

3. Deploy Kafka, backend, workers, and KEDA

4. Get backend URL:
```bash
   minikube service backend --url
```

5. Add this URL as a GitHub webhook

6. Add backend URL in frontend/src/services/api.js

7. Start the frontend
```bash
  npm run dev
```

---

## 9. Challenges & Design Decisions

### 9.1 Stage-Level Distribution
- Initially, entire pipelines were executed by a single worker
- Improved by distributing execution at stage level
- Each stage is dispatched only after previous stage completion

### 9.2 Making Workers Truly Distributed
- Earlier design depended on a shared filesystem
- Backend cloned repo and passed a local path
- This failed for distributed systems

**Fix:** Backend now sends:
- `repo_url`
- `branch`
- `commit_sha`

Workers clone the repository independently and check out the exact commit SHA, ensuring reproducibility and scalability.

### 9.3 Eliminating Manual Setup Complexity
- Previously required multiple terminals
- Hard to manage startup order

**Fix:**
- Full Docker Compose setup
- Services start with dependency checks
- Environment-based configurations added

### 9.4 Kubernetes Execution Model Change
- Local setup: workers used `docker run`
- Kubernetes: workers already run inside containers

**Change:**
- Commands executed directly using `subprocess`
- `image` field in `pipeline.yaml` ignored in K8s mode

### 9.5 Auto-Scaling with KEDA
- Needed dynamic scaling based on load

**Solution:**
- KEDA monitors Kafka consumer lag
- Automatically scales worker replicas between **1–10**

---

## 10. Future Improvements

- Parallel stage execution
- Retry and fault tolerance
- UI dashboard improvements
- Authentication & multi-user support
- Replace SQLite with PostgreSQL
- Advanced scheduling strategies

---

## 11. Conclusion

This project demonstrates a production-style distributed CI/CD system with:

- **Event-driven pipeline triggering** (GitHub webhooks)
- **Distributed execution** using Kafka
- **Scalable workers** with Kubernetes + KEDA
- **Strong consistency** using commit-based execution

It reflects real-world system design patterns used in modern CI/CD platforms.