# Tech Stack — Do Not Deviate From This

## Fixed Choices

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.11 |
| Agent Framework | LangChain | latest |
| LLM | Mistral 7B via Ollama | mistral |
| NLP | spaCy | en_core_web_sm |
| Dashboard | rich | latest |
| Container | Docker + Docker Compose | latest |
| Path matching | fnmatch (stdlib) | built-in |
| HTTP | requests | latest |

## Do Not Use
- OpenAI API (costs money, needs key)
- A second LLM as judge (too slow, too complex)
- Pandas (unnecessary for this project)
- FastAPI/Flask (terminal UI is enough)
- Any vector database
- Any cloud services
- Any paid APIs

## Why Ollama + Mistral
- Runs fully locally, no API key needed
- Free, works offline
- Safe to demo without internet dependency
- Mistral 7B is fast enough for demo purposes