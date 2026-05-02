# distributed-cicd-engine
*A Distributed, Event-Driven CI/CD Platform*

## Overview
We are building a distributed CI/CD system that executes pipeline stages (build, test, deploy) across multiple worker nodes using an event-driven architecture. It leverages Kafka for job distribution and Kubernetes for container orchestration, enabling scalable and fault-tolerant pipeline execution.

---

## Objectives
- Design a distributed CI/CD pipeline engine  
- Implement event-driven job scheduling using Kafka  
- Execute pipelines across containerized workers  
- Deploy applications to Kubernetes  
- Demonstrate scalability and fault tolerance  

---

## Architecture

GitHub Push → Webhook → Pipeline Manager → Kafka → Workers → Kubernetes


---

## Core Components
- **Pipeline Manager**: Parses `pipeline.yaml`, schedules jobs  
- **Kafka**: Handles distributed job queues  
- **Workers**: Execute pipeline commands in containers  
- **Webhook Listener**: Triggers pipelines on GitHub push  
- **Kubernetes**: Hosts workers and deployed applications  

---

## Pipeline Format
```yaml
stages: [build, test, deploy]

jobs:
  build:
    stage: build
    commands:
      - docker build -t myapp .

  test:
    stage: test
    commands:
      - npm test

  deploy:
    stage: deploy
    commands:
      - kubectl apply -f k8s/deployment.yaml
```

## Progress So Far (04/27)
- **Completed**
  - FastAPI backend for pipeline orchestration
  - SQLite-based pipeline, stage, and log persistence
  - Git repository cloning and pipeline parsing
  - Docker-based job execution
  - Real-time log storage and retrieval
  - Vue frontend for pipeline submission and monitoring
  - Automatic polling for near real-time updates
  - CORS integration for frontend-backend communication

- **In Progress**
  - Pipeline history dashboard (GET /pipelines endpoint)
  - Kafka-based distributed job scheduling
  - Worker node orchestration

- **Planned Enhancements**
  - Webhook-triggered pipeline execution
  - Kubernetes deployment automation
  - Horizontal scaling across distributed workers

## How to Run
**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

**Frontend**
```bash
cd frontend
npm install
npm install axios
npm run dev
```

Frontend will be available at http://localhost:5173

## Using the Application
  - Start both backend and frontend services.
  - Open http://localhost:5173 in your browser.
  - Enter a GitHub repository URL.
  - Specify the branch (default: main).
  - Click Run Pipeline.
  - Monitor execution status, stages, and logs in real time.

## Current Status
The project now includes a fully functional single-node CI/CD execution engine with a modern web interface. Users can trigger pipelines, monitor execution progress, and inspect logs in near real time. The next major milestone is transforming the execution engine into a truly distributed system using Kafka and multiple worker nodes.

test
test
