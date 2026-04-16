# distributed-cicd-engine
*A Distributed, Event-Driven CI/CD Platform*

## 📌 Overview
We are building a distributed CI/CD system that executes pipeline stages (build, test, deploy) across multiple worker nodes using an event-driven architecture. It leverages Kafka for job distribution and Kubernetes for container orchestration, enabling scalable and fault-tolerant pipeline execution.

---

## 🎯 Objectives
- Design a distributed CI/CD pipeline engine  
- Implement event-driven job scheduling using Kafka  
- Execute pipelines across containerized workers  
- Deploy applications to Kubernetes  
- Demonstrate scalability and fault tolerance  

---

## 🧠 Architecture

GitHub Push → Webhook → Pipeline Manager → Kafka → Workers → Kubernetes


---

## 🧩 Core Components
- **Pipeline Manager**: Parses `pipeline.yaml`, schedules jobs  
- **Kafka**: Handles distributed job queues  
- **Workers**: Execute pipeline commands in containers  
- **Webhook Listener**: Triggers pipelines on GitHub push  
- **Kubernetes**: Hosts workers and deployed applications  

---

## ⚙️ Pipeline Format
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