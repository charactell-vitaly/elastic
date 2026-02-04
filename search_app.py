import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Load environment variables
load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

app = Flask(__name__)
CORS(app)

# Initialize Elasticsearch client
if ELASTIC_CLOUD_ID:
    es = Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY)
else:
    es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

INDEX_NAME = "multilingual-scale-index"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elastic Multilingual Search | Enterprise Evaluation</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Assistant:wght@400;700&family=Noto+Sans+Arabic:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #0077ff;
            --bg: #090e14;
            --sidebar: #111827;
            --card: #1e293b;
            --text: #f8fafc;
            --text-dim: #94a3b8;
            --accent: #2dd4bf;
            --highlight: #fbbf24;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', 'Assistant', 'Noto Sans Arabic', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar Styles */
        aside {
            width: 320px;
            background: var(--sidebar);
            border-right: 1px solid rgba(255,255,255,0.1);
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
            overflow-y: auto;
            flex-shrink: 0;
        }

        .section-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--primary);
            margin-bottom: 1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filter-group { display: flex; flex-direction: column; gap: 8px; }
        .filter-item {
            padding: 10px 14px;
            border-radius: 10px;
            background: rgba(255,255,255,0.03);
            cursor: pointer;
            transition: 0.2s;
            font-size: 0.9rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid transparent;
        }
        .filter-item:hover { background: rgba(255,255,255,0.08); }
        .filter-item.active { background: rgba(0, 119, 255, 0.1); border: 1px solid var(--primary); color: var(--primary); }

        .test-btn {
            background: rgba(168, 85, 247, 0.1);
            border: 1px solid #a855f7;
            color: #a855f7;
            font-size: 0.8rem;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            text-align: left;
            transition: 0.2s;
        }
        .test-btn:hover { background: rgba(168, 85, 247, 0.2); }

        /* Main Area */
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 2rem 4rem;
            overflow-y: auto;
        }

        .search-container {
            width: 100%;
            max-width: 800px;
            margin: 0 auto 2.5rem;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            display: flex;
            gap: 12px;
            backdrop-filter: blur(20px);
        }

        input {
            flex: 1;
            background: transparent;
            border: none;
            padding: 12px 20px;
            color: white;
            font-size: 1.2rem;
            outline: none;
        }

        .btn-search {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0 2.5rem;
            border-radius: 14px;
            cursor: pointer;
            font-weight: 700;
            font-family: 'Inter';
        }

        #results {
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            display: grid;
            gap: 24px;
        }

        /* Result Cards */
        .card {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 2rem;
            transition: 0.3s;
            display: flex;
            flex-direction: column;
            gap: 12px;
            position: relative;
        }
        .card:hover { border-color: var(--primary); background: rgba(30, 41, 59, 0.6); transform: translateY(-2px); }
        
        .rtl { direction: rtl; text-align: right; }
        .ltr { direction: ltr; text-align: left; }

        .card-header { display: flex; justify-content: space-between; align-items: flex-start; }
        .card-title { font-size: 1.6rem; font-weight: 700; color: #fff; text-decoration: none; }
        
        .card-badges { display: flex; gap: 8px; }
        .badge { font-size: 0.7rem; padding: 4px 10px; border-radius: 6px; font-weight: 700; text-transform: uppercase; }
        .badge-lang { background: rgba(45, 212, 191, 0.1); color: var(--accent); border: 1px solid var(--accent); }
        .badge-cat { background: rgba(0, 119, 255, 0.1); color: var(--primary); border: 1px solid var(--primary); }

        .card-body { font-size: 1.05rem; color: var(--text-dim); line-height: 1.8; }
        
        .explain-box {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 1rem;
            font-family: monospace;
            font-size: 0.85rem;
            color: var(--highlight);
            display: none;
            border: 1px dashed rgba(251, 191, 36, 0.3);
            margin-top: 10px;
        }

        .card-footer { margin-top: 10px; display: flex; align-items: center; justify-content: space-between; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); }
        .footer-info { display: flex; gap: 1rem; font-size: 0.8rem; color: var(--text-dim); }
        .score { color: var(--accent); font-weight: 700; }

        .toggle-explain { cursor: pointer; color: var(--primary); font-size: 0.8rem; font-weight: 600; }

        .no-results { text-align: center; padding: 4rem; color: var(--text-dim); font-size: 1.2rem; }
    </style>
</head>
<body>
    <aside>
        <div class="filter-section">
            <div class="section-title">📊 Content Types</div>
            <div class="filter-group" id="category-filter">
                <div class="filter-item active" onclick="setCat(null, this)">All Content</div>
                <div class="filter-item" onclick="setCat('Parallel Ground Truth', this)">Ground Truth (Parallel)</div>
                <div class="filter-item" onclick="setCat('Background Noise', this)">Background Noise</div>
                <div class="filter-item" onclick="setCat('Protocol', this)">Internal Protocols</div>
            </div>
        </div>
        <div class="filter-section">
            <div class="section-title">🌍 Languages</div>
            <div class="filter-group">
                <div class="filter-item active" onclick="setLang(null, this)">All Languages</div>
                <div class="filter-item" onclick="setLang('en', this)">English</div>
                <div class="filter-item" onclick="setLang('he', this)">Hebrew (עברית)</div>
                <div class="filter-item" onclick="setLang('ar', this)">Arabic (العربية)</div>
            </div>
        </div>

    </aside>

    <main>
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.8rem; margin-bottom: 0.5rem; letter-spacing: -1px;">E5 Multilingual Eval</h1>
            <p style="color: var(--text-dim)">Native <strong>Multilingual E5</strong> (intfloat) performance baseline</p>
        </div>

        <div class="search-container">
            <input type="text" id="query" placeholder="Test semantic mapping..." onkeypress="if(event.key==='Enter') search()">
            <button class="btn-search" onclick="search()">Search</button>
        </div>

        <div id="results"></div>
    </main>

    <script>
        let currentLang = null;
        let currentCat = null;

        function setLang(lang, btn) {
            currentLang = lang;
            document.querySelectorAll('aside .filter-section:nth-child(2) .filter-item').forEach(i => i.classList.remove('active'));
            btn.classList.add('active');
            search();
        }

        function setCat(cat, btn) {
            currentCat = cat;
            document.querySelectorAll('#category-filter .filter-item').forEach(i => i.classList.remove('active'));
            btn.classList.add('active');
            search();
        }

        function runTest(q) {
            document.getElementById('query').value = q;
            search();
        }

        function toggleExplain(id) {
            const box = document.getElementById(`explain-${id}`);
            box.style.display = box.style.display === 'block' ? 'none' : 'block';
        }

        async function search() {
            const query = document.getElementById('query').value;
            const resDiv = document.getElementById('results');
            resDiv.innerHTML = '<div class="no-results">Analyzing semantic space...</div>';

            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        query: query,
                        lang: currentLang,
                        cat: currentCat
                    })
                });
                const data = await response.json();
                resDiv.innerHTML = '';

                if (!data.results || data.results.length === 0) {
                    resDiv.innerHTML = '<div class="no-results">No matches found in the parallel index.</div>';
                    return;
                }

                data.results.forEach((r, idx) => {
                    const isRtl = r.language === 'he' || r.language === 'ar';
                    const card = document.createElement('div');
                    card.className = `card ${isRtl ? 'rtl' : 'ltr'}`;
                    
                    card.innerHTML = `
                        <div class="card-header">
                            <a href="${r.url}" target="_blank" class="card-title">${r.title}</a>
                            <div class="card-badges">
                                <span class="badge badge-lang">${r.language}</span>
                                <span class="badge badge-cat">${r.category}</span>
                            </div>
                        </div>
                        <div class="card-body">${r.content}</div>
                        
                        <div class="explain-box" id="explain-${idx}">
                            <strong>Semantic Match Detail:</strong><br>
                            Matched language: ${r.language.toUpperCase()}<br>
                            Raw Score: ${r.score.toFixed(4)}<br>
                            Source: Wikipedia Summary
                        </div>

                        <div class="card-footer">
                            <div class="footer-info">
                                <span>Relevance: <span class="score">${r.score.toFixed(2)}</span></span>
                                <span>•</span>
                                <span>Wiki ${r.language.toUpperCase()}</span>
                            </div>
                            <div class="toggle-explain" onclick="toggleExplain(${idx})">Explain Match ℹ️</div>
                        </div>
                    `;
                    resDiv.appendChild(card);
                });
            } catch (e) {
                resDiv.innerHTML = `<div class="no-results" style="color: #ef4444">Error: ${e.message}</div>`;
            }
        }

        window.onload = () => search();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search_api():
    data = request.json
    query_text = (data.get('query') or "").strip()
    lang_filter = data.get('lang')
    cat_filter = data.get('cat')

    # 1. Base Query Structure
    if not query_text:
        search_query = {"match_all": {}}
    else:
        # HYBRID SEARCH: Semantic (E5) + Keyword (BM25)
        search_query = {
            "bool": {
                "should": [
                    {
                        "semantic": {
                            "field": "content",
                            "query": query_text,
                            "boost": 2.0  # High weight on semantic understanding
                        }
                    },
                    {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["title^5", "original_title^5"], # Direct keyword boost
                            "type": "best_fields"
                        }
                    }
                ]
            }
        }

    # 2. Add filters (Language, Category)
    filters = []
    if lang_filter:
        filters.append({"term": {"language": lang_filter}})
    if cat_filter:
        filters.append({"term": {"category": cat_filter}})

    body = {
        "query": {
            "bool": {
                "must": [search_query] if query_text else [{"match_all": {}}],
                "filter": filters
            }
        },
        "size": 30 # Increased for better reach
    }

    try:
        resp = es.search(index=INDEX_NAME, body=body)
        results = []
        for hit in resp['hits']['hits']:
            results.append({
                "title": hit['_source'].get('title'),
                "url": hit['_source'].get('url'),
                "content": hit['_source'].get('content'),
                "language": hit['_source'].get('language'),
                "category": hit['_source'].get('category'),
                "score": hit['_score']
            })
        return jsonify({"results": results})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Binding to 0.0.0.0 allows access from other machines on the same network
    app.run(host="0.0.0.0", port=5075)
