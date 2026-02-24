# Hackfest GitHub - Celery Worker Application

A distributed task processing application built with Celery, RabbitMQ, and Redis. This project provides a scalable worker system for asynchronous task processing with real-time monitoring via Flower.

## Prerequisites

- Docker & Docker Compose installed
- Python 3.14+ (for local development)
- Make (optional, for task automation)

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd hackfest-github
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

### 3. Start Services

```bash
docker-compose up -d
```

This will start:

- **RabbitMQ** - Message broker (ports: 5672, 15672)
- **Redis** - Data store (port: 6379)
- **Worker** - Celery worker processes tasks
- **Flower** - Monitoring dashboard (port: 5555)

### 4. Access Interfaces

- **Flower Dashboard** - http://localhost:5555
- **RabbitMQ Management** - http://localhost:15672 (credentials from `.env`)
