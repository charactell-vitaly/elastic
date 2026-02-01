import os
import json
import time
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

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

# Load local model
print("Loading local embedding model...")
model = SentenceTransformer("intfloat/multilingual-e5-small")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elastic Search UI | RAG Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #0077ff;
            --primary-glow: rgba(0, 119, 255, 0.4);
            --bg: #0b111a;
            --sidebar-bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.5);
            --text: #f8fafc;
            --text-dim: #94a3b8;
            --accent: #2dd4bf;
            --star: #fbbf24;
            --magic: #a855f7; /* Purple for AI/Magic */
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Assistant', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar */
        aside {
            width: 320px;
            background: var(--sidebar-bg);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
            flex-shrink: 0;
        }

        .filter-section h3 {
            font-family: 'Outfit';
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .category-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .category-item {
            padding: 12px 15px;
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.2s;
            background: rgba(255,255,255,0.03);
            border: 1px solid transparent;
            font-size: 0.9rem;
        }
        .category-item:hover { background: rgba(255,255,255,0.08); }
        .category-item.active {
            background: rgba(0, 119, 255, 0.15);
            border-color: var(--primary);
            color: var(--primary);
            font-weight: 600;
        }

        /* RAG Info Section */
        .rag-pill {
            background: rgba(168, 85, 247, 0.1);
            border: 1px solid var(--magic);
            color: var(--magic);
            padding: 1rem;
            border-radius: 16px;
            font-size: 0.85rem;
            line-height: 1.5;
        }

        /* Main Content */
        main {
            flex: 1;
            padding: 3rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-y: auto;
        }

        .header { text-align: center; margin-bottom: 3rem; width: 100%; }
        .header h1 { font-family: 'Outfit'; font-size: 3rem; letter-spacing: -2px; }

        .search-area {
            width: 100%;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-bottom: 3rem;
        }

        .search-container {
            background: var(--card-bg);
            border-radius: 24px;
            padding: 10px;
            display: flex;
            gap: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            transition: 0.3s;
        }
        .search-container:focus-within { border-color: var(--primary); box-shadow: 0 0 50px var(--primary-glow); }

        input {
            flex: 1;
            background: transparent;
            border: none;
            padding: 15px 20px;
            color: white;
            font-size: 1.3rem;
            outline: none;
        }

        .btn {
            padding: 0 2.5rem;
            border-radius: 16px;
            cursor: pointer;
            font-weight: 800;
            font-family: 'Outfit';
            border: none;
            transition: 0.2s;
        }
        .btn-primary { background: var(--primary); color: white; }
        .btn-magic { 
            background: linear-gradient(135deg, var(--magic), #7c3aed); 
            color: white; 
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .btn:hover { filter: brightness(1.2); transform: translateY(-2px); }

        /* Magic Answer Panel */
        #magic-answer-box {
            width: 100%;
            max-width: 850px;
            margin-bottom: 3rem;
            display: none;
            animation: fadeIn 0.8s ease-out;
        }

        .ai-card {
            background: linear-gradient(160deg, rgba(168, 85, 247, 0.1) 0%, rgba(30, 41, 59, 0.8) 100%);
            border: 1px solid var(--magic);
            border-radius: 24px;
            padding: 2.5rem;
            position: relative;
            overflow: hidden;
        }

        .ai-card::before {
            content: "AI ANSWER";
            position: absolute;
            top: 20px;
            left: 20px;
            font-size: 0.7rem;
            font-family: 'Outfit';
            opacity: 0.5;
            letter-spacing: 0.2rem;
        }

        #ai-text { font-size: 1.25rem; line-height: 1.8; color: #fff; }

        .source-tag {
            font-size: 0.8rem;
            background: rgba(168, 85, 247, 0.2);
            color: var(--magic);
            padding: 4px 12px;
            border-radius: 20px;
            margin-top: 1.5rem;
            display: inline-block;
        }

        /* Results */
        #results { width: 100%; max-width: 850px; display: grid; gap: 20px; }

        .card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.05);
            transition: 0.3s;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .card:hover { transform: scale(1.01); border-color: rgba(255,255,255,0.2); }
        .card-title { font-weight: 700; font-size: 1.4rem; color: #fff; }
        .card-meta { display: flex; gap: 10px; align-items: center; }
        .card-cat { font-size: 0.7rem; background: rgba(0,119,255,0.1); color: var(--primary); padding: 3px 10px; border-radius: 6px; }
        .card-body { font-size: 0.95rem; color: var(--text-dim); line-height: 1.7; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .loader {
            display: none;
            width: 30px;
            height: 30px;
            border: 2px solid rgba(255,255,255,0.1);
            border-top-color: var(--magic);
            border-radius: 50%;
            animation: spin 1s infinite linear;
            margin: 0 auto;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

    </style>
</head>
<body>
    <aside>
        <div class="filter-section">
            <h3>📂 Index Filter</h3>
            <ul class="category-list">
                <li class="category-item active" onclick="setCategory(null, this)">All Docs</li>
                <li class="category-item" onclick="setCategory('Geography', this)">Geography</li>
                <li class="category-item" onclick="setCategory('Science', this)">Science</li>
            </ul>
        </div>

        <div class="filter-section">
            <h3>🤖 RAG Engine</h3>
            <div class="rag-pill">
                <strong>How it works:</strong><br>
                1. Elastic finds context.<br>
                2. AI processes snippet.<br>
                3. You get a direct answer.<br>
                <em>Using Mock-RAG for demo.</em>
            </div>
        </div>
    </aside>

    <main>
        <div class="header">
            <h1>Elastic RAG Demo</h1>
            <p style="color:var(--text-dim)">Search -> Context -> Answer</p>
        </div>

        <div class="search-area">
            <div class="search-container">
                <input type="text" id="query" placeholder="Ask a question about Israel or Science..." onkeypress="if(event.key==='Enter') doRag()">
                <button class="btn btn-magic" onclick="doRag()">Magic Answer ✨</button>
            </div>
            <div style="text-align: center; font-size: 0.8rem; color: var(--text-dim)">
                Try: "Tell me about the history of Jerusalem?" or "What is Science?"
            </div>
        </div>

        <div id="magic-answer-box">
            <div class="ai-card">
                <div id="ai-text">Generating...</div>
                <div id="ai-source" class="source-tag">Source: Wikipedia</div>
            </div>
        </div>

        <div id="results-title" style="margin-bottom: 1.5rem; font-weight: 700; color: var(--text-dim); display: none;">Supporting Documents:</div>
        <div id="results"></div>
    </main>

    <script>
        let category = null;

        function setCategory(cat, btn) {
            category = cat;
            document.querySelectorAll('.category-item').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        async function doRag() {
            const q = document.getElementById('query').value;
            if (!q) return;

            const answerBox = document.getElementById('magic-answer-box');
            const aiText = document.getElementById('ai-text');
            const resDiv = document.getElementById('results');
            const resTitle = document.getElementById('results-title');

            answerBox.style.display = 'block';
            aiText.innerHTML = '<div class="loader" style="display:block"></div>';
            resDiv.innerHTML = '';
            resTitle.style.display = 'block';

            try {
                const response = await fetch('/rag', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ query: q, category })
                });
                const data = await response.json();

                // Display AI Answer
                aiText.innerHTML = data.answer;
                document.getElementById('ai-source').innerText = `Grounded by: ${data.source_title}`;

                // Display retrieved results
                data.results.forEach(r => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.innerHTML = `
                        <div class="card-title">${r.title}</div>
                        <div class="card-meta">
                            <span class="card-cat">${r.category}</span>
                            <span style="font-size:0.7rem; color:var(--text-dim)">Score: ${r.score.toFixed(2)}</span>
                        </div>
                        <div class="card-body">${r.content}</div>
                    `;
                    resDiv.appendChild(card);
                });

            } catch (err) {
                aiText.innerHTML = `Error: ${err.message}`;
            }
        }
    </script>
</body>
</html>
"""

# MOCK RAG LOGIC
# In a real app, this would call OpenAI or Gemini
def simulate_ai_answer(query, context, title):
    time.sleep(1) # Fake thinking
    
    if "ירושלים" in title or "ירושלים" in context or "Jerusalem" in query.lower():
        return f"Jerusalem is one of the world's oldest cities with a rich history spanning millennia. According to the fetched content from Wikipedia, it is central to many cultures and has undergone significant historical transitions. Based on this documentation, politics in Jerusalem remain a key area of global interest."
    elif "מדע" in title or "Science" in query.lower():
        return f"Science (מדע) is the systematic study of the physical and natural world through observation and experiment. The Wikipedia context indexed in Elasticsearch highlights that modern science has evolved through centuries of research and remains the primary driver of human technological progress."
    elif "ישראל" in title or "Israel" in query.lower():
        return f"Israel is a country in the Middle East with a deep history. The retrieval from your Elastic index shows it has a rich cultural and technological landscape. Based on the Wikipedia summary, it emerged as a modern independent state with a unique synthesis of ancient and modern elements."
    
    return f"Based on the documents found in your index: {context[:200]}..."

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/rag', methods=['POST'])
def rag_api():
    data = request.json
    query_text = data.get('query')
    category_filter = data.get('category')

    # 1. RETRIEVAL STEP
    # Use the cloud index for best semantic context
    index_name = "ct-multilingual-semantic-index"
    
    semantic_clause = {
        "semantic": {
            "field": "content",
            "query": query_text
        }
    }
    
    search_body = {"query": semantic_clause}
    if category_filter:
        search_body = {
            "query": {
                "bool": {
                    "must": [semantic_clause],
                    "filter": [{"term": {"category": category_filter}}]
                }
            }
        }

    try:
        response = es.search(index=index_name, body=search_body, size=3)
        hits = response['hits']['hits']
        
        if not hits:
            return jsonify({"answer": "I couldn't find any relevant data in your index to answer that.", "results": [], "source_title": "N/A"})

        # Top hit becomes our 'context'
        top_hit = hits[0]['_source']
        context = top_hit['content']
        source_title = top_hit['title']

        # 2. GENERATION STEP (Simulated)
        answer = simulate_ai_answer(query_text, context, source_title)

        results = []
        for hit in hits:
            results.append({
                "title": hit['_source'].get('title'),
                "content": hit['_source'].get('content'),
                "category": hit['_source'].get('category'),
                "score": hit['_score']
            })

        return jsonify({
            "answer": answer,
            "results": results,
            "source_title": source_title
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000)
