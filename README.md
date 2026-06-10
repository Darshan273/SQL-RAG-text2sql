# 🤖 SQL RAG(text2sql)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Model: Llama-3](https://img.shields.io/badge/LLM-Llama--3--70B-purple.svg)](https://groq.com/)

An intelligent SQL RAG text-to-SQL system that converts natural language questions into optimized SQL queries, executes them against a PostgreSQL database, and returns human-readable insights.

---

## 📑 Table of Contents

- [🚀 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [⚡ Performance Highlights](#-performance-highlights)
- [🏗️ System Architecture](#-system-architecture)
- [📊 Database Schema](#-database-schema)
- [🎬 Demo](#-demo)
- [🛠️ Tech Stack](#-tech-stack)
- [📂 Project Structure](#-project-structure)
- [📋 Prerequisites](#-prerequisites)
- [⚙️ Installation](#-installation)
- [🔐 Environment Variables](#-environment-variables)
- [🏃 Running the Project](#-running-the-project)
- [📡 API Reference](#-api-reference)
- [📖 Usage Examples](#-usage-examples)
- [🧪 Testing](#-testing)
- [🚢 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [⚠️ Known Issues / Limitations](#-known-issues--limitations)
- [🗺️ Roadmap](#-roadmap)
- [📄 License](#-license)
- [👤 Author / Credits](#-author--credits)

---

## 🚀 Overview

The **Text-to-SQL System** solves the barrier between non-technical users and complex databases. By leveraging state-of-the-art LLMs (via Groq) and agentic workflows (via LangGraph), this system does[...]

---

## ✨ Key Features

- **Agentic Workflow**: Uses LangGraph to manage a multi-step process including generation, validation, and self-correction.
- **Natural Language Insights**: Converts raw SQL results back into human-friendly explanations.
- **Read-Only Safety**: Integrated `readonly_guard` to prevent destructive operations (INSERT/UPDATE/DELETE).
- **Auto-Retry & Validation**: Automatically fixes syntax errors or schema mismatches before returning results.
- **High Performance**: Powered by Groq's Llama-3-70B for near-instant SQL generation.
- **Traceability**: Full integration with LangSmith for debugging and monitoring agent chains.

---

## ⚡ Performance Highlights

### 🎯 Token Efficient
- **Optimized Prompts**: Carefully crafted system prompts that minimize token usage while maintaining accuracy
- **Schema-Aware Context**: Only relevant schema information is sent to the LLM, reducing unnecessary tokens
- **Smart Caching**: Leverages LangGraph's state management to avoid redundant LLM calls

### ⏱️ Lower Time Consumption
- **Groq's Lightning-Fast Inference**: Powered by Groq's specialized hardware for near-instant SQL generation (typically **<500ms** per query)
- **Async Architecture**: FastAPI with asyncpg ensures non-blocking database operations
- **Minimal Retry Overhead**: Smart validation logic reduces the need for multiple LLM calls

**Result**: Complete query execution (question → SQL → results → answer) typically completes in **1-2 seconds**, even for complex queries!

---

## 🏗️ System Architecture

```mermaid
graph TD
    START((Start)) --> RG[Read-Only Guard]
    RG -- Safe --> SUP[Supervisor]
    RG -- Violation --> END((End))
    
    SUP --> GEN[SQL Generator]
    GEN --> VAL[Validator]
    
    VAL -- Invalid --> RET[Retry Logic]
    RET --> VAL
    
    VAL -- Valid --> EXE[SQL Executor]
    VAL -- Error --> END
    
    EXE --> FMT[Result Formatter]
    FMT --> END
```

---

## 📊 Database Schema

Here's the ecommerce database schema used in the demo:

![Database Schema](demo/postgres%20-%20ecommerce%20-%20public.png)

This schema includes:
- **users** - User account information
- **products** - Product catalog
- **orders** - Customer orders
- **order_items** - Line items in orders
- **categories** - Product categories
- And other related tables for a complete ecommerce system

---

## 🎬 Demo

### Demo Workflow Screenshots

**Step 1: Initial Query Interface**
![Demo Step 1](demo/Screenshot%202026-06-04%20140803.png)

**Step 2: Query Processing & SQL Generation**
![Demo Step 2](demo/Screenshot%202026-06-10%20170707.png)

**Step 3: Query Execution & Results**
![Demo Step 3](demo/Screenshot%202026-06-10%20170740.png)

**Step 4: Advanced Query Example**
![Demo Step 4](demo/Screenshot%202026-06-10%20171716.png)

**Step 5: Complex Analysis Query**
![Demo Step 5](demo/Screenshot%202026-06-10%20171807.png)

**Step 6: Multi-Table Join Query**
![Demo Step 6](demo/Screenshot%202026-06-10%20171834.png)

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Primary development language |
| **Web Framework** | FastAPI | High-performance asynchronous API |
| **Orchestration** | LangGraph | State management and agentic workflow |
| **LLM Provider** | Groq | High-speed inference for Llama-3 models |
| **ORM / DB Driver** | SQLAlchemy / asyncpg | Async database connection and execution |
| **SQL Analysis** | sqlglot | SQL parsing and dialect conversion |
| **Validation** | Pydantic | Schema validation and settings management |

---

## 📂 Project Structure

```text
.
├── .env                    # Environment variables (API keys, DB URLs)
├── .langgraph_api          # LangGraph deployment configuration
├── app/                    # Core application directory
│   ├── main.py             # Entry point: FastAPI application and routes
│   ├── config.py           # Configuration and Pydantic settings
│   ├── db/                 # Database connection and session management
│   ├── graph/              # LangGraph definition (nodes, edges, state)
│   ├── schemas/            # Pydantic models for API and Tools
│   └── tools/              # Custom tools for the agent (DB introspection, etc.)
├── demo/                   # Demo screenshots and database schema
├── langgraph.json          # LangGraph CLI configuration
├── requirements.txt        # Python dependency list
├── tests/                  # Pytest suite for unit and integration tests
└── README.md               # Project documentation
```

---

## 📋 Prerequisites

- **Python**: 3.10 or 3.11
- **PostgreSQL**: Version 13+ (Required for query execution)
- **Groq API Key**: Obtain from [Groq Cloud](https://console.groq.com/)
- **LangSmith API Key** (Optional): For tracing and observability

---

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/text-to-sql-main.git
   cd text-to-sql-main
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Environment Variables:**
   Copy the `.env` template and fill in your details:
   ```bash
   cp .env.example .env  # Or create a new .env file
   ```

---

## 🔐 Environment Variables

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | **Yes** | - | Your Groq Cloud API key |
| `DATABASE_URL` | **Yes** | - | SQLAlchemy URL (e.g., `postgresql+asyncpg://user:pass@host:port/db`) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | The LLM model to use |
| `LANGSMITH_TRACING` | No | `false` | Enable/Disable LangChain tracing |
| `LANGSMITH_API_KEY` | No | - | LangSmith project API key |
| `LANGSMITH_PROJECT` | No | `text-to-sql-dev` | Name of the LangSmith project |

---

## 🏃 Running the Project

### Development Mode
Run the FastAPI server with hot-reload:
```bash
uvicorn app.main:app --reload
```

### Production Mode
Run using Gunicorn or high-performance Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker
(🔧 TODO: Add Dockerfile and docker-compose.yml for production deployment)

---

## 📡 API Reference

### 1. Execute Query
- **Method**: `POST`
- **Path**: `/query`
- **Body**:
  ```json
  {
    "question": "What are the total sales for last month?"
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "answer": "Total sales for last month were $45,230.12.",
    "sql": "SELECT SUM(amount) FROM sales WHERE date >= '2024-04-01'...",
    "tool_used": "execute_sql",
    "row_count": 1,
    "readonly_violation": false
  }
  ```

### 2. Health Check
- **Method**: `GET`
- **Path**: `/health`
- **Response**: `{ "status": "ok", "model": "llama-3.3-70b-versatile" }`

---

## 📖 Usage Examples

### Using `curl`
```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"question": "How many users signed up in the last 7 days?"}'
```

### Using Python `requests`
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"question": "List the top 5 customers by revenue."}
)
print(response.json()["answer"])
```

---

## 🧪 Testing

The project uses `pytest` with `pytest-asyncio` for testing the asynchronous API and graph logic.

1. **Run all tests:**
   ```bash
   pytest
   ```

2. **Run with coverage:**
   ```bash
   pytest --cov=app tests/
   ```

---

## 🚢 Deployment

### Deploy to Render / Railway
1. Connect your GitHub repository.
2. Add the environment variables listed in the [Environment Variables](#-environment-variables) section.
3. Set the start command to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## 🤝 Contributing

1. **Fork** the project.
2. **Clone** your fork (`git clone ...`).
3. **Branch** off for your feature (`git checkout -b feature/amazing-feature`).
4. **Commit** your changes (`git commit -m 'Add amazing feature'`).
5. **Push** to the branch (`git push origin feature/amazing-feature`).
6. Open a **Pull Request**.

---

## ⚠️ Known Issues / Limitations

- **Schema Complexity**: Extremely complex schemas with 50+ tables might require fine-tuning or RAG-based context injection for the supervisor.
- **Dialect Support**: Optimized primarily for **PostgreSQL**. Support for MySQL or SQLite is experimental via `sqlglot`.
- **Latency**: While Groq is fast, complex multi-turn retries can lead to 2-3s response times.

---

## 🗺️ Roadmap

- [ ] Support for multiple database dialects (MySQL, Snowflake).
- [ ] RAG-based schema fetching for large databases.
- [ ] User authentication and API key management.
- [ ] Frontend dashboard for query history and visualization.
- [ ] Streaming responses for the "answering" phase.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 👤 Author / Credits

- **Author**: Darshan
- **Contact**: darshanjain2202@gmail.com
- **Acknowledgments**: 
  - Thanks to the [LangChain](https://langchain.com) team for LangGraph.
  - Thanks to [Groq](https://groq.com) for providing lightning-fast inference.
