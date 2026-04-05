# Python Script Packaging Guide

This document outlines the best ways to package and run the Python URL downloader script using bash.

## 📦 Available Execution Methods

### 1. **Shell Wrapper Scripts** (Recommended for Local Development)

**Files:** `downloader.sh`, `url-to-md.sh`

```bash
# Simple execution
./downloader.sh https://example.com
./url-to-md.sh https://example.com -o my_folder

# Show help
./downloader.sh --help
./url-to-md.sh --help
```

**Pros:**
- ✅ Simple and direct
- ✅ Works immediately without installation
- ✅ Good for development and testing
- ✅ Can be symlinked to `/usr/local/bin` for global access

**Cons:**
- ❌ Requires being in the project directory (unless symlinked)
- ❌ Not as portable as installed packages

### 2. **uv run with Python Scripts** (Simple Development)

```bash
# Direct execution via uv
uv run python downloader/main.py https://example.com
uv run python downloader/url_downloader.py https://example.com -o my_folder

# Alternative (if scripts are in root)
uv run python main.py https://example.com
```

**Pros:**
- ✅ No additional setup required
- ✅ Works with uv's virtual environment management
- ✅ Good for development

**Cons:**
- ❌ Verbose command line
- ❌ Requires being in project directory

### 3. **Console Scripts via Local Installation** (Recommended for Single User)

**Setup:**
```bash
# Install in editable mode
uv pip install -e .
```

**Usage:**
```bash
# Use installed console scripts
uv run downloader https://example.com
uv run url-to-md https://example.com -o my_folder
```

**Pros:**
- ✅ Clean, short commands
- ✅ Editable installation updates automatically
- ✅ Proper Python package structure
- ✅ Works with uv's environment management

**Cons:**
- ❌ Only available within the project's virtual environment

### 4. **Global Tool Installation** (Recommended for System-wide Access)

**Setup:**
```bash
# Install as global uv tool
uv tool install .
```

**Usage:**
```bash
# Use commands globally (no uv run needed)
downloader https://example.com
url-to-md https://example.com -o my_folder

# Uninstall when no longer needed
uv tool uninstall downloader
```

**Pros:**
- ✅ Available globally from any directory
- ✅ Clean commands without prefixes
- ✅ No need for `uv run`
- ✅ Isolated installation

**Cons:**
- ❌ Requires installation step
- ❌ Updates require reinstallation

## 🏆 Best Practices by Use Case

### For **Development & Testing**
```bash
# Use shell wrappers for quick iteration
./downloader.sh https://example.com
```

### For **Local Project Usage**
```bash
# Install locally and use console scripts
uv pip install -e .
uv run downloader https://example.com
```

### For **System-wide Tool**
```bash
# Install as global tool
uv tool install .
downloader https://example.com
```

### For **Distribution/Sharing**
```bash
# Package for PyPI or git installation
uv build
# Or share via git URL: uv tool install git+https://github.com/user/repo.git
```

## 🔧 Project Structure

```
downloader/
├── downloader/                # Python package
│   ├── __init__.py
│   ├── main.py               # Main CLI interface
│   └── url_downloader.py     # Core functionality
├── downloader.sh             # Shell wrapper for main
├── url-to-md.sh             # Shell wrapper for url_downloader
├── pyproject.toml           # Package configuration with console scripts
├── .gitignore              # Excludes downloads/, .venv, etc.
└── README.md
```

## ⚙️ Console Scripts Configuration

**pyproject.toml:**
```toml
[project.scripts]
downloader = "downloader.main:main"
url-to-md = "downloader.url_downloader:main"

[tool.setuptools]
packages = ["downloader"]
```

## 📝 Installation Commands Summary

| Method | Setup Command | Usage Command |
|--------|---------------|---------------|
| Shell Scripts | `chmod +x *.sh` | `./downloader.sh <url>` |
| uv run | None | `uv run python downloader/main.py <url>` |
| Local Install | `uv pip install -e .` | `uv run downloader <url>` |
| Global Tool | `uv tool install .` | `downloader <url>` |

## 🌟 Recommended Approach

**For most users:** Use **Global Tool Installation** (`uv tool install .`)
- Provides clean, globally accessible commands
- Easy to install, update, and remove
- No need to remember project paths or prefixes

**For developers:** Start with **Shell Wrappers** during development, then switch to **Local Installation** for testing the packaged version.