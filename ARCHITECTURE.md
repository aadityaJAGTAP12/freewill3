# System Architecture

## Components (build in this order)

### 1. Intent Compiler
Input: raw user prompt string
Output: structured policy object

{
  "original_prompt": "summarize files in /documents",
  "allowed_tools": ["read_file"],
  "allowed_paths": ["/documents/**"],
  "denied_tools": ["write_file", "shell_exec", "web_request"],
  "denied_paths": ["~/.ssh/**", "/etc/**", "*.env"],
  "allowed_domains": [],
  "task_keywords": ["summarize", "documents", "read"]
}

Use spaCy for keyword extraction.
Derive allowed/denied lists from verb + path in prompt.
Keep it simple — this does not need an LLM.

### 2. LangChain Agent
- Model: Ollama with mistral:7b (local, no API key needed)
- Tools to implement:
  - read_file(path: str) → reads and returns file contents
  - write_file(path: str, content: str) → writes to file
  - shell_exec(command: str) → runs shell command, 
    returns output
  - web_request(url: str) → makes HTTP GET, 
    returns response text
- Run inside Docker container for safety
- Wire BaseCallbackHandler to fire on every agent step

### 3. Telemetry Capture (inside callback handler)
On every agent action, capture:
{
  "step": int,
  "timestamp": ISO string,
  "tool_called": str,
  "tool_args": dict,
  "file_paths": [str],  # extracted from args
  "urls": [str],        # extracted from args  
  "commands": [str],    # extracted from args
  "previous_tools": [str]  # last 5 tools called
}

Do NOT capture agent_thought — not reliable.

### 4. Policy Engine
Deterministic allow/deny rules from Intent Compiler output.
Runs BEFORE drift scorer.
Returns:
{
  "policy_violation": bool,
  "violation_type": str,  # "tool", "path", "domain"
  "violation_detail": str,
  "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
}

Rules:
- Tool not in allowed_tools → CRITICAL violation
- Path matches denied_paths pattern → CRITICAL violation  
- Domain not in allowed_domains → HIGH violation
- Path outside allowed_paths → HIGH violation

### 5. Drift Scorer
Runs after Policy Engine (only if no CRITICAL violation).
Returns multidimensional score:
{
  "scope_drift": float,      # 0.0-1.0
  "tool_drift": float,       # 0.0-1.0
  "privilege_drift": float,  # 0.0-1.0
  "network_drift": float,    # 0.0-1.0
  "sequence_risk": float,    # 0.0-1.0
  "overall_risk": float      # weighted average
}

Scoring logic:
- scope_drift: is current path within allowed_paths? 
  0.0=yes, 1.0=no
- tool_drift: is tool in allowed_tools? 
  0.0=yes, 1.0=no
- privilege_drift: does tool/path require higher privilege 
  than task warrants? rule-based
- network_drift: unexpected network access? 
  0.0=no network, 1.0=external domain not in allowed
- sequence_risk: does last N tools match known attack 
  sequence patterns?

Known attack sequences to detect:
- read_file → shell_exec → web_request (exfiltration)
- read_file → write_file → shell_exec (tamper+execute)
- shell_exec → web_request → delete_file (c2+cleanup)

Overall risk = weighted average:
weights = {scope:0.25, tool:0.30, privilege:0.20, 
           network:0.15, sequence:0.10}

### 6. Risk Aggregator
Combines Policy Engine + Drift Scorer outputs.
Decision logic:
- Policy CRITICAL violation → AUTO BLOCK, no user prompt
- Overall risk > 0.75 → INTERRUPT, ask user
- Overall risk 0.50-0.75 → WARN, log, continue
- Overall risk < 0.50 → ALLOW, log

### 7. Interrupt Engine
When INTERRUPT or AUTO BLOCK:
- Raise exception in LangChain callback BEFORE tool executes
- Display to user:
  
  ⚠️  BEHAVIORAL DRIFT DETECTED — Step N
  
  Original task: "[original prompt]"
  Current action: tool_name(args)
  
  Risk Breakdown:
  Scope Drift:     [score] [bar]
  Tool Drift:      [score] [bar]  
  Privilege Drift: [score] [bar]
  Network Drift:   [score] [bar]
  Overall Risk:    [score]
  
  Reason: [violation detail]
  
  [A] Allow once  [B] Block  [K] Kill session

### 8. Dashboard
Terminal UI using Python rich library.
Two panels:
- Left: live event feed (every step, color coded by risk)
- Right: current risk scores + interrupt prompts
Bottom: audit log (full session history, exportable)

Color coding:
- Green: risk < 0.3
- Yellow: risk 0.3-0.6  
- Orange: risk 0.6-0.75
- Red: risk > 0.75 or policy violation