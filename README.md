# HR Leave Management Agent

A local MCP (Model Context Protocol) server for employee leave management, paired with a terminal-based AI agent powered by **Groq + LangGraph** — no Claude Desktop required.

---

## Architecture

```
┌─────────────────────┐        MCP (streamable-http)        ┌────────────────────────────────┐
│   client.py         │ ──────────────────────────────────► │   emp_leave_managing_server.py │
│   LangGraph Agent   │ ◄────────────────────────────────── │   FastMCP Server               │
│   (Groq LLM)        │        tool calls / responses       │   (leave data)                 │
└─────────────────────┘                                      └────────────────────────────────┘
```

---

## Features

- **Apply leave** — submit a leave request for an employee
- **Approve / Reject leave** — process pending requests with approver name and comments
- **Leave balance** — check remaining leave days for any employee
- **Leave history** — view full or filtered (APPROVED / REJECTED / PENDING) leave history per employee
- **Pre-populated demo data** — Alice (E001) and Bob (E002) with realistic historical records
- **Email prompt generator** — generate professional leave notification emails via MCP prompt

---

## Project Structure

```
hr_agent/
├── emp_leave_managing_server.py  # MCP server (FastMCP) — tools, resources, prompts
├── client.py                     # Terminal agent — Groq LLM + LangGraph ReAct agent
├── pyproject.toml                # Dependencies (uv)
├── .env                          # API keys (not committed)
└── README.md
```

---

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- A [Groq API key](https://console.groq.com/)

---

## Setup

1. **Clone / open the project**

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Create a `.env` file** in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

---

## Running

Open **two terminals** in the project directory.

**Terminal 1 — start the MCP server:**
```bash
uv run emp_leave_managing_server.py
```
The server starts at `http://localhost:8000/mcp`.

**Terminal 2 — start the agent:**
```bash
uv run client.py
```

---

## Example Conversations

```
You: What is Alice's leave balance?
Agent: Alice (E001) currently has 20 days of leave remaining.

You: Show me Bob's leave history
Agent: Bob (E002) has 3 historical leave records:
  - H005: 4 days — Wedding ceremony (APPROVED)
  - H006: 2 days — Home renovation (REJECTED)
  - H007: 1 day  — Child school event (APPROVED)

You: Apply 3 days leave for E001 for a medical checkup
Agent: Leave request submitted successfully. Leave ID: 1

You: Show only rejected leaves for E001
Agent: Alice has 1 rejected leave record:
  - H003: 5 days — Personal travel (REJECTED, reason: Critical project deadline)

You: Approve leave 1 as Manager_Sarah
Agent: Leave approved. Alice's remaining balance is now 17 days.
```

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `apply_leave(employee_id, days, reason)` | Submit a new leave request |
| `approve_leave(leave_id, approver)` | Approve a pending request |
| `reject_leave(leave_id, approver, comments)` | Reject a pending request |
| `get_leave_balance(employee_id)` | Get remaining leave days |
| `get_leave_history(employee_id, status_filter?)` | Get leave history (optional filter: APPROVED / REJECTED / PENDING) |

## MCP Resources

| URI | Description |
|-----|-------------|
| `leave://status/{leave_id}` | Get status of a specific leave request |
| `employee://{employee_id}` | Get employee profile and balance |

---

## Demo Employees

| ID | Name | Leave Balance |
|----|------|---------------|
| E001 | Alice | 20 days |
| E002 | Bob | 15 days |

---

## Notes

- All data is **in-memory** — restarting the server resets it to the initial state
- If you are behind a **corporate proxy** with SSL inspection, the client already handles it with `verify=False` on the Groq HTTP client
- The LLM model used is `openai/gpt-oss-120b` via Groq (configurable in `client.py`)