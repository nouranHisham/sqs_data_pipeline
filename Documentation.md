# SQS Data Pipeline – Documentation

## Overview

This project implements a simple **ETL (Extract–Transform–Load) pipeline** that consumes messages from an **AWS SQS queue**, transforms them into a unified trip structure, and persists the results into a **PostgreSQL database**.

To avoid using real AWS infrastructure, **Localstack** is used to emulate AWS SQS locally.  
The entire setup is reproducible using **Docker and Docker Compose**.

The ETL consumer is designed to be stateless and idempotent.

---

## Architecture

**Flow:**

1. **Message Generator** pushes events to an SQS queue (Localstack).
2. **ETL Consumer (Python)**:
   - Polls SQS messages
   - Transforms different event formats into a unified schema
   - Stores events in PostgreSQL
   - Deletes processed messages from the queue
3. **PostgreSQL** persists the transformed events.

Message Generator
↓
SQS (Localstack)
↓
Python ETL Consumer
↓
PostgreSQL

---

## Technology Choices

### Language: Python 3

Python was chosen because:
- Excellent AWS SDK support via **boto3**
- Simple and readable ETL logic
- Strong PostgreSQL integration (`psycopg2`)
- Fast iteration and debugging
- Widely used for data engineering tasks

### Database: PostgreSQL

- Reliable relational database
- JSONB support for semi-structured data (`trip`)
- Easy Docker-based setup
- Cross-platform compatibility (Linux / macOS / Windows)

---

## Requirements

### System Requirements
- Docker
- Docker Compose
- Python 3.9+

### Python Dependencies
- `boto3`
- `psycopg2-binary`

---

## Environment Configuration

All configuration values are centralized in `config.py`.

### AWS / Localstack
```python
AWS_REGION = "ap-south-1"
AWS_ENDPOINT_URL = "http://localstack:4566"
AWS_ACCESS_KEY = "test"
AWS_SECRET_KEY = "test"

SQS_MAX_MESSAGES = 10
SQS_WAIT_TIME = 5
```

### Database (PostgreSQL)
```python
DB_HOST = "postgres"
DB_PORT = 5432
DB_NAME = "events_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
```

### App Settings
```python
POLLING_SLEEP_SECONDS = 5
```
---

## Database Schema

The following table is automatically created on startup:

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    mail TEXT NOT NULL,
    name TEXT NOT NULL,
    trip JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);
```
- Upsert logic ensures the tool can be safely run multiple times.
- Records are only updated if data actually changes.

---

## Supported Event Formats

The consumer supports multiple input message structures and converts them into a unified format.

### Unified Output Structure

```json
{
  "id": 1,
  "mail": "aaa@gmail.com",
  "name": "AAA SSS",
  "trip": {
    "departure": "A",
    "destination": "D",
    "start_date": "2022-10-10 12:15:00",
    "end_date": "2022-10-10 13:55:00"
  }
}
```

---

## Supported Input Types

1. Route-based messages
    - Uses route[]
    - Computes trip duration from segments

2. Location-based messages
    - Uses UNIX timestamps
    - Converts timestamps to UTC datetime

Transformation logic is implemented in `src/transformer.py`

---

## How to Build & Run

From the project root directory, run `make go`

### This command performs the following steps automatically:

1. Builds the ETL Docker image
2. Starts required infrastructure:
    - Localstack (AWS SQS)
    - PostgreSQL
3. Runs the ETL consumer container
4. Consumes all messages from the SQS queue
5. Stores transformed events into PostgreSQL
6. Exits automatically once the queue has been empty for 30 seconds

---

## Stopping and Cleaning Up

To stop all running containers and clean up resources, run `make down`

---

## Verifying the Output

To inspect the persisted data in PostgreSQL, run `docker-compose exec postgres psql -U postgres -d events_db`

### Example query

```sql
SELECT
  id,
  mail,
  name,
  trip->>'departure'   AS departure,
  trip->>'destination' AS destination,
  trip->>'start_date'  AS start_date,
  trip->>'end_date'    AS end_date,
  created_at,
  updated_at
FROM events;
```

---

### How the Tool Works

1. Wait for the SQS queue to exist
2. Ensure the database and table are created
3. Polls up to 10 messages per request
4. Processes and stores messages consumed from the SQS queue
5. Deletes messages only after successful processing
6. Handles malformed messages safely
7. Supports re-runs without duplicating data
8. Exit automatically after the queue is empty for 30 seconds

---

## Error Handling

- Invalid JSON → message deleted
- Processing error → message kept for retry
- PostgreSQL unavailable → retries with backoff
- Queue not ready → waits until available

---

## Challenges & Solutions

1. SQS Readiness
    - Problem: Consumer might start before SQS queue exists
    - Solution: Implemented wait_for_queue() with retries

2. PostgreSQL Startup Timing
    - Problem: App starting before DB is ready
    - Solution: wait_for_postgres() with retry logic

3. Multiple Event Formats
    - Problem: Messages had different schemas
    - Solution: Centralized transformation logic with clear branching

4. Idempotency
    - Problem: Tool must be safely re-runnable
    - Solution: PostgreSQL UPSERT with change detection

---

## Project Structure

.
├── DOCUMENTATION.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── src/
│   ├── main.py
│   ├── config.py
│   ├── sqs_client.py
│   ├── transformer.py
│   └── database_loader.py

---

