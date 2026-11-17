# Khidmah SQL Assistant

A natural-language interface to a MySQL database, built with LlamaIndex + Groq. Ask
questions in plain English, get answers backed by generated SQL.

## Components

- **`app.py`** — the working backend. A Quart (async Flask) API that wraps a
  `NLSQLTableQueryEngine` in a ReAct agent, exposing `POST /query`.
- **`streamlit_app.py`** — a chat UI that calls the `app.py` API.
- **`connect.py`** — standalone script to sanity-check the MySQL connection.
- **`groq_code.py`** — an older/alternate version of the backend (Flask instead of
  Quart, real HuggingFace embeddings instead of disabled embeddings, a hardcoded
  table filter). **Not currently working** — it still references a Groq model
  (`meta-llama/llama-4-scout-17b-16e-instruct`) that's no longer available. Not
  needed to run the app; kept for reference.

## Prerequisites

- Python virtualenv at `myenv/` (already set up)
- MySQL running locally with a read-only user that can access the target database
- A valid Groq API key

## Setup

```
C:\groq_khidmah\myenv\Scripts\activate.bat
pip install -r requirements.txt
pip install quart hypercorn
copy .env.example .env
```

Then edit `.env` and fill in `GROQ_API_KEY` and the `DB_*` values. All scripts
(`app.py`, `groq_code.py`, `connect.py`) read their settings from `.env`. Never
commit `.env` — it's listed in `.gitignore`. Run `python connect.py` to check the
database settings.

## Running

Two terminals, both with the venv activated.

**Terminal 1 — backend:**
```
python app.py
```
Wait for `Running on http://127.0.0.1:5000`.

**Terminal 2 — UI:**
```
streamlit run streamlit_app.py
```
Opens a chat window in your browser.

## Notes on Groq models

Groq periodically retires/renames models. If you see `openai.NotFoundError: ...
model_not_found`, check what your API key currently has access to:

```
python -c "
import requests
r = requests.get('https://api.groq.com/openai/v1/models',
    headers={'Authorization': 'Bearer <your-key>'})
for m in r.json()['data']:
    print(m['id'])
"
```

Then update `GROQ_MODEL` in `.env` accordingly. Avoid the
`openai/gpt-oss-*` family for this ReAct pipeline — those models are prone to
emitting a spontaneous tool-call even when no tools were sent in the request,
which Groq's server rejects with `Tool choice is none, but model called a tool`.

## Known limitations

- No conversation memory: each question is answered independently. The backend
  doesn't retain any state between requests, and the Streamlit chat history is
  purely a local display list, never sent back to the API.
- Broad "list everything" style questions (e.g. "list all customers") force the
  response synthesizer through multiple sequential LLM refine calls and can be
  slow — narrower or aggregate questions resolve much faster.
- Groq's free/on-demand tier enforces output-tokens-per-minute limits per model;
  `max_tokens` is capped in `app.py` to stay under them.
