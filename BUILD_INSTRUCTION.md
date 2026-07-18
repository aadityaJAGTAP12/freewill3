# Build Instructions

## Order of Implementation

Build in exactly this order. Do not skip ahead.

### Step 1: Project Setup
- Python 3.11
- Docker + Docker Compose
- Dependencies:
  langchain
  langchain-community  
  ollama
  spacy
  scikit-learn
  rich
  requests
  python-dotenv

- Pull spaCy model: python -m spacy download en_core_web_sm
- Pull Ollama model: ollama pull mistral

### Step 2: Intent Compiler
File: src/intent_compiler.py
- Function: compile_intent(user_prompt: str) -> dict
- Use spaCy to extract nouns, verbs, file paths
- Map to allowed/denied tools and paths
- Return structured policy object
- Write 5 unit tests for different prompt types

### Step 3: LangChain Agent + Tools
File: src/agent.py
File: src/tools.py
- Implement 4 tools as LangChain Tool objects
- Wire up agent with mistral via Ollama
- Implement BaseCallbackHandler subclass
- Confirm callbacks fire and print on every step
- Test with a safe prompt before adding monitor

### Step 4: Telemetry Capture
File: src/telemetry.py
- Inside callback handler, capture structured event 
  per step
- Extract paths/urls/commands from tool args
- Store session history as list of events
- No agent thoughts — observable signals only

### Step 5: Policy Engine  
File: src/policy_engine.py
- Function: check_policy(event: dict, policy: dict) -> dict
- Implement 4 rules (tool, path, domain, privilege)
- Use fnmatch for path pattern matching
- Return violation object
- Write unit tests for each rule type

### Step 6: Drift Scorer
File: src/drift_scorer.py
- Function: score_drift(event: dict, 
                        policy: dict, 
                        history: list) -> dict
- Implement 5 scoring dimensions
- Implement 3 sequence pattern detectors
- Return multidimensional score dict
- Write unit tests with sample event sequences

### Step 7: Risk Aggregator
File: src/risk_aggregator.py
- Function: aggregate_risk(policy_result: dict, 
                           drift_scores: dict) -> dict
- Implement decision logic (auto block/interrupt/warn/allow)
- Return decision + full reasoning

### Step 8: Interrupt Engine
File: src/interrupt_engine.py
- Raise LangChain ToolException to block tool execution
- Display formatted interrupt prompt to user
- Handle user input (A/B/K)
- Log decision to audit log

### Step 9: Dashboard
File: src/dashboard.py
- Use rich.live + rich.table + rich.panel
- Left panel: live event feed
- Right panel: current risk scores
- Bottom: audit log
- Update on every agent step

### Step 10: Docker Setup
File: Dockerfile
File: docker-compose.yml
- Python 3.11 slim base
- Install all dependencies
- Mount /documents as safe read directory
- Mount /attack as directory containing 
  malicious test files
- Expose no external ports

### Step 11: Attack Scenario Runner
File: src/attack_runner.py
- Script that runs each attack scenario 
  automatically
- Records: which step triggered alert, 
  what scores were, what was blocked
- Used to generate demo evidence

## File Structure
src/
  intent_compiler.py
  agent.py
  tools.py
  telemetry.py
  policy_engine.py
  drift_scorer.py
  risk_aggregator.py
  interrupt_engine.py
  dashboard.py
  attack_runner.py
tests/
  test_intent_compiler.py
  test_policy_engine.py
  test_drift_scorer.py
data/
  documents/          # safe files for normal demo
  attack/             # files containing injections
Dockerfile
docker-compose.yml
requirements.txt
README.md
