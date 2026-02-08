# leader-toolbox

A knowledge base-powered chat application that provides accurate, evidence-backed responses for leadership tasks and decision-making.

## Overview

**leader-toolbox** is an AI-powered chat web application designed to help leaders access and leverage organizational knowledge effectively. Built with FastAPI and advanced vector search capabilities, it provides:

- **Evidence-based responses**: All answers are grounded in your knowledge base with proper citations
- **Vector-powered search**: Uses semantic similarity to find relevant information across documents
- **Leadership focus**: Specifically designed to support leadership tasks and decision-making processes
- **Privacy-first design**: Local deployment with configurable data retention and PII protection

### Key Features

- 🔍 **Semantic Search**: Advanced vector-based retrieval using sentence transformers
- 📚 **Knowledge Base Integration**: Ingest documents and retrieve contextual information
- 🎯 **Citation Support**: Every response includes source references and excerpts
- 🔒 **Privacy Controls**: Configurable data retention and automatic PII redaction
- 🚀 **Fast Deployment**: Local-first with easy scaling options
- 🧪 **Test Coverage**: Comprehensive test suite for reliable operation

## Architecture

The application uses a modern vector-based retrieval architecture:

```
User Query → FastAPI Backend → Vector Embedding → FAISS Search → Response + Citations
```

**Core Components**:
- **Backend**: FastAPI web service (`backend/fastapi_chat.py`)
- **Vector Store**: FAISS for efficient similarity search
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Text Processing**: Configurable chunking with overlap (1000/200 chars)
- **Retrieval**: Top-K results with similarity thresholds

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
