import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()
es = Elasticsearch(os.getenv('ELASTIC_URL'), api_key=os.getenv('ELASTIC_API_KEY'), request_timeout=300)

INDEX_NAME = "multilingual-scale-index"
INFERENCE_ID = ".multilingual-e5-small-elasticsearch"

# 1. Clean up
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)

# 2. Create mapping
mapping = {
    "mappings": {
        "properties": {
            "title": {"type": "text"},
            "content": {
                "type": "semantic_text",
                "inference_id": INFERENCE_ID
            }
        }
    }
}
es.indices.create(index=INDEX_NAME, body=mapping)
print("Index created.")

# 3. Index one doc
doc = {
    "title": "E5 Test",
    "content": "This is a test of the multilingual E5 model in Hebrew: שלום עולם"
}

try:
    res = es.index(index=INDEX_NAME, document=doc, refresh=True)
    print(f"✅ Indexed! ID: {res['_id']}")
except Exception as e:
    print(f"❌ Failed: {e}")
