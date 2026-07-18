"""Intent Compiler — extracts structured policy from a raw user prompt.

Uses spaCy en_core_web_sm for keyword extraction only (no LLM).
Maps extracted verbs to LangChain tools, extracts file paths,
and returns a structured policy object matching the schema in
SAMPLE_EVENTS.md.
"""

from __future__ import annotations

import re
from typing import Any

import spacy
from spacy.language import Language

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PATH_PATTERN = re.compile(r"(?:/|~/|\./)[\w/.~\-]+")
_URL_PATTERN = re.compile(r"https?://([\w.-]+)(?:/[\w/.~\-]*)?")
_DOMAIN_PATTERN = re.compile(r"([\w-]+\.)+[\w-]{2,}")

# Map of verb lemmas → tool names
VERB_TO_TOOL: dict[str, str] = {
    # read_file triggers
    "read": "read_file",
    "view": "read_file",
    "summarize": "read_file",
    "list": "read_file",
    "cat": "read_file",
    "show": "read_file",
    "display": "read_file",
    "check": "read_file",
    "examine": "read_file",
    "inspect": "read_file",
    "look": "read_file",
    "get": "read_file",
    "find": "read_file",
    "open": "read_file",
    "scan": "read_file",
    "review": "read_file",
    # write_file triggers
    "write": "write_file",
    "create": "write_file",
    "edit": "write_file",
    "save": "write_file",
    "update": "write_file",
    "modify": "write_file",
    "change": "write_file",
    "append": "write_file",
    "delete": "write_file",
    "remove": "write_file",
    "overwrite": "write_file",
    "generate": "write_file",
    "produce": "write_file",
    "output": "write_file",
    # shell_exec triggers
    "run": "shell_exec",
    "execute": "shell_exec",
    "shell": "shell_exec",
    "bash": "shell_exec",
    "sh": "shell_exec",
    "command": "shell_exec",
    "script": "shell_exec",
    "pipeline": "shell_exec",
    "compile": "shell_exec",
    "install": "shell_exec",
    "deploy": "shell_exec",
    "start": "shell_exec",
    "stop": "shell_exec",
    "restart": "shell_exec",
    # web_request triggers
    "fetch": "web_request",
    "download": "web_request",
    "curl": "web_request",
    "wget": "web_request",
    "request": "web_request",
    "upload": "web_request",
    "send": "web_request",
    "post": "web_request",
    "scrape": "web_request",
}

# Tools known to the system
ALL_TOOLS: set[str] = {
    "read_file",
    "write_file",
    "shell_exec",
    "web_request",
}

# Sensitive paths always denied regardless of user prompt
# (matches the spec in SAMPLE_EVENTS.md exactly)
ALWAYS_DENIED_PATHS: list[str] = [
    "~/.ssh/**",
    "/etc/**",
    "**/.env",
    "**/id_rsa",
    "**/authorized_keys",
]

# ---------------------------------------------------------------------------
# SpaCy model loader (lazy singleton)
# ---------------------------------------------------------------------------

_nlp: Language | None = None


def _get_nlp() -> Language:
    """Return a cached spaCy Language instance."""
    global _nlp  # noqa: PLW0603
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_tools(prompt: str) -> set[str]:
    """Determine which tools the user intends to allow based on prompt verbs.

    Uses spaCy lemmatized verb forms to match against VERB_TO_TOOL.
    Falls back to simple word matching if spaCy parsing is unavailable.
    """
    nlp = _get_nlp()
    doc = nlp(prompt)
    allowed: set[str] = set()

    # Collect all lemmas (verbs, but also check nouns in case of noun-verb
    # ambiguity)
    lemmas: list[str] = []
    for token in doc:
        if token.pos_ in {"VERB", "NOUN", "PROPN"} or token.lemma_ in VERB_TO_TOOL:
            lemmas.append(token.lemma_.lower())

    # Also split the raw prompt into lowercase words as a fallback
    raw_words = set(re.findall(r"[a-zA-Z_]\w*", prompt.lower()))

    # Match against verb-tool map
    for lemma in lemmas:
        if lemma in VERB_TO_TOOL:
            allowed.add(VERB_TO_TOOL[lemma])

    # Fallback: match raw words
    for word in raw_words:
        if word in VERB_TO_TOOL:
            allowed.add(VERB_TO_TOOL[word])

    return allowed


def _extract_paths(prompt: str) -> list[str]:
    """Extract filesystem paths mentioned in the prompt.

    Matches patterns starting with /, ~/, or ./
    Skips paths that are part of URLs (preceded by ://).
    """
    matches: list[str] = []
    for m in _PATH_PATTERN.finditer(prompt):
        start = m.start()
        # Skip paths that are part of URLs (preceded by schema like https://)
        if start >= 1 and prompt[start - 1] == ":":
            continue
        matches.append(m.group(0))
    return list(set(matches))


def _extract_domains(prompt: str) -> list[str]:
    """Extract domain names mentioned in the prompt.

    Covers both full URLs and bare domain names.
    """
    domains: set[str] = set()

    # From full URLs
    for match in _URL_PATTERN.finditer(prompt):
        domains.add(match.group(1))

    # Bare domain names (not part of URLs, not file paths)
    for match in _DOMAIN_PATTERN.finditer(prompt):
        candidate = match.group(0)
        # Skip if it looks like a file path
        if not any(candidate.startswith(p) for p in ("/", "~", ".")):
            # Skip common false positives
            if candidate not in {"txt", "md", "py", "json", "yml", "yaml", "csv"}:
                domains.add(candidate)

    return sorted(domains)


def _extract_keywords(prompt: str) -> list[str]:
    """Extract meaningful keywords from the prompt using spaCy.

    Returns lemmatized tokens for nouns, proper nouns, verbs, and adjectives
    that are not stop words or punctuation.
    """
    nlp = _get_nlp()
    doc = nlp(prompt)
    keywords: list[str] = []

    for token in doc:
        if not token.is_stop and not token.is_punct and not token.is_space:
            if token.pos_ in {"NOUN", "PROPN", "VERB", "ADJ"}:
                lemma = token.lemma_.lower()
                # Skip very short tokens and pure numbers
                if len(lemma) > 1 and not lemma.isdigit():
                    keywords.append(lemma)

    return keywords


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compile_intent(user_prompt: str) -> dict[str, Any]:
    """Compile a user prompt into a structured policy object.

    Parameters
    ----------
    user_prompt : str
        The raw user prompt describing the task for the agent.

    Returns
    -------
    dict
        Structured policy object with keys:
        - original_prompt : str
        - allowed_tools : list[str]
        - allowed_paths : list[str]
        - denied_tools : list[str]
        - denied_paths : list[str]
        - allowed_domains : list[str]
        - task_keywords : list[str]
    """
    # 1. Determine allowed tools from verbs
    allowed_tools_set = _extract_tools(user_prompt)

    # If no tools could be determined, default to the safest subset:
    # read-only access. If the user says something vague but file-related,
    # allow read_file.
    if not allowed_tools_set:
        allowed_tools_set = {"read_file"}

    allowed_tools = sorted(allowed_tools_set)
    denied_tools = sorted(ALL_TOOLS - allowed_tools_set)

    # 2. Extract paths
    extracted_paths = _extract_paths(user_prompt)

    # Build allowed_paths: if the user specified a path, scope to that path.
    # Otherwise allow all paths (the policy engine and drift scorer will
    # still enforce denied_paths).
    if extracted_paths:
        # Convert bare paths to glob patterns
        allowed_paths = []
        for p in extracted_paths:
            # If path ends with /, glob everything inside
            if p.endswith("/"):
                allowed_paths.append(f"{p}**")
            # If path already looks like a file (has extension), exact match
            elif "." in p.split("/")[-1]:
                allowed_paths.append(p)
            # Otherwise treat as directory
            else:
                allowed_paths.append(f"{p}/**")
    else:
        allowed_paths = ["**"]

    # 3. Extract URLs / domains
    extracted_domains = _extract_domains(user_prompt)

    # 4. Extract keywords
    keywords = _extract_keywords(user_prompt)

    # 5. Assemble policy object
    policy: dict[str, Any] = {
        "original_prompt": user_prompt,
        "allowed_tools": allowed_tools,
        "allowed_paths": allowed_paths,
        "denied_tools": denied_tools,
        "denied_paths": ALWAYS_DENIED_PATHS[:],
        "allowed_domains": extracted_domains,
        "task_keywords": keywords,
    }

    return policy
