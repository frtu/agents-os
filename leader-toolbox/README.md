# leader-toolbox

## Overview

A Chat web application allowing to retrieve info from KB (Knowledge Base) and accomplish some leadership
 tasks.

## Runtime

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Start server

```bash
uvicorn backend.fastapi_chat:app --reload --port 8002
```

http://localhost:8002/ingest_text?name=project_faq&content=PS:Payment system

### Test

```bash
pytest -q
```

### Troubleshooting

#### FAISS installation - command 'swig'

Symptom :

```
ERROR: Could not build wheels for faiss-cpu, which is required to install pyproject.toml-based projects
<OR>
error: command 'swig' failed: No such file or directory
```

Resolution :

```
brew uninstall swig
brew install swig
```

#### FAISS installation - 'swig command exit 1'

Symptom :

```
swig command exit 1
```

Resolution :

Fix faiss version to `==1.7.4`

```
"faiss-cpu==1.7.4"
```
