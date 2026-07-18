# Agent Behavioral Monitor

A runtime monitoring system that detects when an AI agent (LangChain + Mistral 7B) drifts from its original task intent. Built for a 5-day hackathon.

## The Problem

AI agents are given real permissions to read files, write files, execute shell commands, and make network requests. When an agent reads untrusted content (prompt injection), it can be manipulated into performing actions the user never intended — stealing SSH keys, exfiltrating data, tampering with files.

Existing tools (Falco, NeMo Guardrails, etc.) don't compare agent behavior against the *original user intent*. This tool fills that gap.

## Architecture

```
User Prompt → Intent Compiler → Policy Object
                                    ↓
Agent Action → Telemetry Capture → Policy Engine → Drift Scorer → Risk Aggregator → Interrupt Engine
                                    ↓                                                    ↓
                               Dashboard (rich TUI)                              Block / Warn / Allow
```

Seven components, built in order:
1. **Intent Compiler** — extracts user intent from prompt using spaCy
2. **LangChain Agent + Tools** — 4 tools (read_file, write_file, shell_exec, web_request) with Ollama/mistral
3. **Telemetry Capture** — callback handler recording every agent action
4. **Policy Engine** — deterministic allow/deny rules
5. **Drift Scorer** — multidimensional risk scoring
6. **Risk Aggregator** — combines policy + drift into decision
7. **Interrupt Engine** — blocks dangerous tool calls
8. **Dashboard** — rich terminal UI showing live monitoring

## Setup

### Prerequisites
- Python 3.11
- Docker + Docker Compose (for containerized execution)
- Ollama (for local LLM)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd agent-behavioral-monitor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Pull Ollama model
ollama pull mistral
```

### Quick Start

```bash
# Copy and configure environment
cp .env.example .env

# Run the dashboard (with a test prompt)
python src/main.py "summarize files in /documents"
```

## Project Structure

```
├── src/
│   ├── intent_compiler.py    # Step 2
│   ├── agent.py              # Step 3
│   ├── tools.py              # Step 3
│   ├── telemetry.py          # Step 4
│   ├── policy_engine.py      # Step 5
│   ├── drift_scorer.py       # Step 6
│   ├── risk_aggregator.py    # Step 7
│   ├── interrupt_engine.py   # Step 8
│   ├── dashboard.py          # Step 9
│   └── attack_runner.py      # Step 11
├── tests/
│   ├── test_intent_compiler.py
│   ├── test_policy_engine.py
│   └── test_drift_scorer.py
├── data/
│   ├── documents/            # Safe files for normal demo
│   └── attack/               # Files containing injections
├── Dockerfile                # Step 10
├── docker-compose.yml        # Step 10
├── requirements.txt
├── .env.example
└── README.md
```

## Attack Scenarios

1. **Prompt Injection via File** — Agent reads a file containing injected instructions that tell it to exfiltrate SSH keys
2. **Kill Chain / Sequence Attack** — Gradual escalation: read → shell → web exfiltration
3. **Normal Task (No False Positive)** — Verifies the monitor doesn't flag legitimate usage

## Tech Stack

- Python 3.11
- LangChain (agent framework)
- Mistral 7B via Ollama (local LLM)
- spaCy (NLP for intent extraction)
- rich (terminal dashboard)
- Docker (containerized execution)
