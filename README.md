# EcomAgentOS / CommercePilot

CommercePilot is a production-oriented e-commerce Multi-Agent backend
for read-only business analytics and controlled business actions.

It combines:

- LangGraph stateful workflows
- Supervisor-based agent routing
- Safe Text-to-SQL
- PostgreSQL
- Human-in-the-loop approval
- Durable checkpointing
- FastAPI + SSE streaming
- Langfuse observability
- Benchmark-driven evaluation

# EcomAgentOS / CommercePilot

CommercePilot is a production-oriented e-commerce Multi-Agent backend
for read-only business analytics and controlled business actions.

It combines:

- LangGraph stateful workflows
- Supervisor-based agent routing
- Safe Text-to-SQL
- PostgreSQL
- Human-in-the-loop approval
- Durable checkpointing
- FastAPI + SSE streaming
- Langfuse observability
- Benchmark-driven evaluation


## Architecture

```mermaid
flowchart TD

    U[Client] --> API[FastAPI + SSE]

    API --> S[Supervisor]

    S -->|Read-only analytics| A[Analytics Agent]
    S -->|Business action| B[Action Agent]
    S -->|Out of scope| X[Unsupported]

    A --> SC[Schema Context]
    SC --> SQL[Text-to-SQL]
    SQL --> GUARD[SQLGlot Safety Guard]
    GUARD --> DB[(Business PostgreSQL)]

    GUARD -->|Failure| RETRY[Repair Loop]
    RETRY --> SQL

    DB --> ANSWER[Answer Generator]

    B --> PLAN[Action Planner]
    PLAN --> PRODUCT[Load Current State]
    PRODUCT --> RISK[Risk Assessment]
    RISK --> HITL[Human Approval]

    HITL -->|Approve| WRITE[Idempotent Action]
    HITL -->|Reject| CANCEL[Cancel]

    WRITE --> DB

    API --> CP[(PostgreSQL Checkpoint)]
    HITL --> CP

    S -. traces .-> LF[Langfuse]
    A -. traces .-> LF
    B -. traces .-> LF


这张图已经足够。

不要再画 30 个框。

---

# 十七、README 核心能力

```markdown
## Core Capabilities

### 1. Supervisor Multi-Agent Routing

The supervisor routes requests between:

- Analytics Agent
- Action Agent
- Unsupported fallback

Routing output is structured with Pydantic rather than free-form text.

### 2. Safe Text-to-SQL

The analytics workflow includes:

1. live database schema reflection;
2. business semantic context;
3. structured SQL generation;
4. SQLGlot AST validation;
5. table whitelist;
6. PostgreSQL read-only transactions;
7. statement timeout;
8. result row limits;
9. error-feedback SQL repair.

### 3. Human-in-the-loop Actions

Database writes are isolated from read-only analytics.

Price changes follow:

Action Plan → Current State → Risk Assessment → Interrupt →
Human Approval → Idempotent Write.

The workflow can pause, survive a process restart, and resume using
the same LangGraph thread.

### 4. Durable Execution

Agent state is persisted using PostgreSQL-backed LangGraph
checkpoints instead of process-local memory.

### 5. Evaluation

CommercePilot evaluates:

- routing accuracy;
- SQL execution success;
- result accuracy;
- task success;
- retry rate;
- repair success rate;
- latency.

### 6. Observability

Langfuse traces cover:

- supervisor routing;
- SQL generation;
- validation;
- database execution;
- retries;
- answer generation;
- action planning.

## Evaluation

The benchmark uses a frozen synthetic e-commerce PostgreSQL snapshot
and manually verified executable Gold SQL.

### Metrics

| Metric | Result |
| --- | ---: |
| Routing Accuracy | See latest evaluation report |
| SQL Execution Success | See latest evaluation report |
| Result Accuracy | See latest evaluation report |
| Task Success Rate | See latest evaluation report |
| Retry Rate | See latest evaluation report |
| Repair Success Rate | See latest evaluation report |

Evaluation reports are generated locally under:

`evals/reports/`

## Safety Boundaries

CommercePilot separates read and write paths.

### Analytics

Generated SQL is:

- parsed with SQLGlot;
- limited to one statement;
- restricted to SELECT-style queries;
- restricted to whitelisted tables;
- executed inside a read-only PostgreSQL transaction;
- protected with a statement timeout and output row limit.

### Actions

Business writes:

- cannot be executed directly by the LLM;
- require a structured action schema;
- load the current database state before approval;
- require human approval;
- validate stale approval state before execution;
- use idempotent write behavior where possible.

## Quick Start

### 1. Clone

```bash
git clone <your-repository>
cd ecom-agent-os

### 2.Configure
cp .env.example .env

### 3. Start
docker compose up --build -d

### 4. Health Check
curl http://127.0.0.1:8000/health

### 5. Stream Analytics
curl -N \
  -X POST \
  http://127.0.0.1:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"request":"最近30天耳机品类GMV是多少？"}'


---

# 二十一、README HITL Demo

继续：

```markdown
## Human-in-the-loop Demo

Start an action:

```bash
curl -N \
  -X POST \
  http://127.0.0.1:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"request":"把SKU-0001价格调整为299元"}'

The workflow returns an approval_required event and persists its state.
Resume:
curl -N \
  -X POST \
  http://127.0.0.1:8000/api/v1/approve/stream \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id":"<thread-id>",
    "decision":"approve",
    "comment":"approved by operator"
  }'

## Tech Stack

| Layer | Technology |
| --- | --- |
| Workflow | LangGraph |
| LLM API | OpenAI-compatible async client |
| API | FastAPI |
| Streaming | SSE |
| Business DB | PostgreSQL |
| Checkpoint DB | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| SQL Safety | SQLGlot |
| Validation | Pydantic |
| Observability | Langfuse |
| Packaging | uv |
| Deployment | Docker Compose |
| CI | GitHub Actions |
| Testing | pytest |
| Lint / Format | Ruff |

## Failure Analysis

Evaluation is not limited to aggregate accuracy.

Failed cases are categorized and inspected using Langfuse traces.

Typical failure categories include:

- time-window interpretation;
- business metric semantics;
- join selection;
- schema hallucination;
- SQL execution errors.

Failure cases are preserved instead of removing difficult samples
from the benchmark.