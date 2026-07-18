# Sample Events and Data Structures

## Sample Policy Object (output of Intent Compiler)
{
  "original_prompt": "summarize files in /documents",
  "allowed_tools": ["read_file"],
  "allowed_paths": ["/documents/**"],
  "denied_tools": ["write_file", "shell_exec", "web_request"],
  "denied_paths": ["~/.ssh/**", "/etc/**", "**/.env", 
                   "**/id_rsa", "**/authorized_keys"],
  "allowed_domains": [],
  "task_keywords": ["summarize", "files", "documents"]
}

## Sample Telemetry Event (output of Callback Handler)
{
  "step": 3,
  "timestamp": "2025-01-01T10:00:03Z",
  "tool_called": "read_file",
  "tool_args": {"path": "~/.ssh/authorized_keys"},
  "file_paths": ["~/.ssh/authorized_keys"],
  "urls": [],
  "commands": [],
  "previous_tools": ["read_file", "read_file"]
}

## Sample Policy Engine Output
{
  "policy_violation": true,
  "violation_type": "path",
  "violation_detail": "Path ~/.ssh/authorized_keys matches 
                       denied pattern ~/.ssh/**",
  "severity": "CRITICAL"
}

## Sample Drift Scores Output
{
  "scope_drift": 1.0,
  "tool_drift": 0.0,
  "privilege_drift": 0.9,
  "network_drift": 0.0,
  "sequence_risk": 0.3,
  "overall_risk": 0.61
}

## Sample Risk Aggregator Output
{
  "decision": "AUTO_BLOCK",
  "reason": "CRITICAL policy violation: path denial",
  "policy_result": {...},
  "drift_scores": {...},
  "recommended_action": "Block tool execution immediately"
}

## Sample Audit Log Entry
{
  "step": 3,
  "timestamp": "2025-01-01T10:00:03Z",
  "event": {...},
  "policy_result": {...},
  "drift_scores": {...},
  "decision": "AUTO_BLOCK",
  "user_action": "BLOCK"
}