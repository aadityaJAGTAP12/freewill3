# Project Context

## What Problem Are We Solving

AI agents (LangChain, AutoGPT, Claude Code etc.) are given 
real permissions to act on a machine — read files, write 
files, execute shell commands, make network requests.

The danger: an agent can be manipulated by content it reads 
(prompt injection) and start doing things the user never 
asked for. By the time it's obvious something went wrong, 
data may already be stolen or deleted.

## Why Existing Tools Don't Solve This

- Falco/Tetragon: watches kernel syscalls, has no concept 
  of agent, task, or intent
- Prempti: intercepts tool calls against static rules, but 
  has zero semantic context — doesn't know what the user 
  originally asked for
- NeMo Guardrails: filters input/output text, doesn't watch 
  runtime behavior
- Garak/PyRIT: offensive testing tools, not runtime monitors

## The Gap We Are Filling

No existing tool asks:
"Is the agent still doing what the user originally asked?"

Most tools ask:
"Is this specific tool call allowed by a static rule?"

We are building the layer that:
1. Establishes what the user intended before any untrusted 
   input is read
2. Monitors every agent action against that original intent
3. Interrupts the agent before the next tool call executes 
   when drift is detected

## Key Insight

We do NOT depend on agent internal thoughts or reasoning 
(not reliably exposed by all LLMs). We only use observable 
signals: tool name, tool arguments, file paths, URLs, 
shell commands, timestamps.

## This Is A Hackathon Project — 5 Days

Scope is intentionally narrow. One agent framework, 
one demo scenario set, working end to end. No feature 
creep.