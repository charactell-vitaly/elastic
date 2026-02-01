# Multilingual Semantic Search with Elasticsearch E5

A Flask-based semantic search application demonstrating Elasticsearch's **multilingual E5 model** for cross-lingual document retrieval. Search in **English**, **Hebrew**, or **Arabic** and find semantically relevant results across all languages.

## Features

- **Cross-lingual Semantic Search**: Query in one language, find results in all three
- **Wikipedia Indexer**: Automatically fetches and indexes articles from Wikipedia
- **Modern Flask UI**: Clean, responsive interface with RTL support
- **Parallel Topics**: Same subjects indexed across languages for benchmarking

---

## Project Structure

```
elastic/
├── search_app.py       # Flask web application (main entry point)
├── indexer.py          # Wikipedia article fetcher and Elasticsearch indexer
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Your actual credentials (not in git)
└── .gitignore          # Git exclusions
```

### Core Files

| File | Purpose |
|------|---------|
| `search_app.py` | Flask server with search UI. Runs on port 5000. |
| `indexer.py` | Fetches Wikipedia articles and bulk-indexes them into Elasticsearch with E5 embeddings. |
| `requirements.txt` | Python packages: Flask, elasticsearch, python-dotenv, wikipedia-api |
| `.env.example` | Template for required environment variables |

---

## Prerequisites

1. **Python 3.10+**
2. **Elasticsearch Cloud account** with:
   - E5 multilingual inference endpoint deployed
   - An index configured with `semantic_text` field type

---

## Deployment Guide

### 1. Clone the Repository

```bash
git clone https://github.com/charactell-vitaly/elastic.git
cd elastic
```

### 2. Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Elasticsearch credentials:

```env
ELASTIC_CLOUD_ID=your-deployment:base64encodedstring
ELASTIC_API_KEY=your-api-key
```

### 5. Index Wikipedia Articles (First Time Only)

```bash
python indexer.py
```

This will:
- Fetch ~270 Wikipedia articles across English, Hebrew, and Arabic
- Index them with E5 semantic embeddings
- Takes approximately 10-15 minutes

### 6. Run the Application

```bash
python search_app.py
```

The app will be available at: **http://localhost:5000**

---

## Running as a Background Service (Linux)

### Using systemd

Create `/etc/systemd/system/elastic-search.service`:

```ini
[Unit]
Description=Elastic Semantic Search App
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/elastic
Environment="PATH=/path/to/elastic/.venv/bin"
ExecStart=/path/to/elastic/.venv/bin/python search_app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable elastic-search
sudo systemctl start elastic-search
```

### Using Screen (Quick Option)

```bash
screen -S elastic
python search_app.py
# Press Ctrl+A, then D to detach
```

Reattach later with: `screen -r elastic`

---

## Network Access

By default, Flask binds to `localhost`. To allow access from other machines:

Edit `search_app.py` and change:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

Then ensure port 5000 is open in your firewall:

```bash
# Ubuntu/Debian
sudo ufw allow 5000

# CentOS/RHEL
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure virtual environment is activated |
| Connection refused to Elasticsearch | Check `.env` credentials and network access |
| Indexer stuck | Wikipedia API may be rate-limited; wait and retry |
| Hebrew/Arabic display issues | Ensure browser supports RTL; the UI handles this automatically |

---

## License

MIT
