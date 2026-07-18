# Do Not Do — Hard Constraints

## Scope
- Do not add more than 4 tools to the agent
- Do not add memory monitoring
- Do not add content influence detection
- Do not add a web UI (terminal only)
- Do not add a second LLM judge
- Do not add cloud integrations
- Do not add more than 3 attack scenarios

## Technical
- Do not use agent.thought or internal reasoning 
  in any detection logic — not reliable
- Do not use OpenAI or any paid API
- Do not use a vector database
- Do not use async unless absolutely necessary
- Do not over-engineer the drift scorer — 
  simple weighted average is enough

## Architecture
- Do not merge components into one file
- Do not skip unit tests for policy engine 
  and drift scorer
- Do not add features not in BUILD_INSTRUCTIONS.md
- Do not change the tech stack in TECH_STACK.md

## When In Doubt
Build the simpler version.
A working simple version beats a broken complex version.