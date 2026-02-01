from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

if ELASTIC_CLOUD_ID:
    es = Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY)
else:
    es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

INDEX_NAME = "multilingual-scale-index"

def trace_einstein_rank(query_text):
    print(f"\n--- Tracing Rank for: '{query_text}' ---")
    
    search_query = {
        "semantic": {
            "field": "content",
            "query": query_text
        }
    }
    
    # Increase size to find the document if it's ranked low
    resp = es.search(index=INDEX_NAME, query=search_query, size=100)
    
    found = False
    for i, hit in enumerate(resp['hits']['hits']):
        src = hit['_source']
        if src['language'] == 'he' and 'איינשטיין' in src['title']:
            print(f"✅ FOUND HEBREW EINSTEIN at Rank {i+1} (Score: {hit['_score']})")
            found = True
            # Also show what's at rank 1
            r1 = resp['hits']['hits'][0]['_source']
            print(f"Rank 1: [{r1['language']}] {r1['title']} (Score: {resp['hits']['hits'][0]['_score']})")
            break
            
    if not found:
        print("❌ Hebrew Einstein NOT FOUND in top 100")

if __name__ == "__main__":
    trace_einstein_rank("Who is Albert Einstein?")
    trace_einstein_rank("Einstein")
