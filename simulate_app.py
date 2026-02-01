from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv
import json

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

if ELASTIC_CLOUD_ID:
    es = Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY)
else:
    es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

INDEX_NAME = "multilingual-scale-index"

def simulate_search_app(query_text, lang_filter=None):
    print(f"\n--- Simulating Search App: Query='{query_text}', Lang='{lang_filter}' ---")
    
    search_query = {
        "semantic": {
            "field": "content",
            "query": query_text if query_text else "*" 
        }
    }

    if not query_text:
        search_query = {"match_all": {}}

    filters = []
    if lang_filter:
        filters.append({"term": {"language": lang_filter}})

    if filters:
        body = {
            "query": {
                "bool": {
                    "must": [search_query] if query_text else [],
                    "filter": filters
                }
            }
        }
        if not query_text:
             body["query"]["bool"]["must"] = {"match_all": {}}
    else:
        body = {"query": search_query}

    try:
        resp = es.search(index=INDEX_NAME, body=body, size=20)
        print(f"Total Hits: {resp['hits']['total']['value']}")
        for i, hit in enumerate(resp['hits']['hits']):
            src = hit['_source']
            print(f"  {i+1}. [{src['language']}] {src['title']} (Score: {hit['_score']})")
        
        if resp['hits']['total']['value'] == 0:
            print("  !!! NO RESULTS FOUND !!!")
            
    except Exception as e:
        print(f"  !!! ERROR: {e}")

if __name__ == "__main__":
    # Test 1: English query + Hebrew filter
    simulate_search_app("Einstein", "he")
    
    # Test 2: English query (no filter)
    simulate_search_app("Einstein")
    
    # Test 3: Hebrew query (no filter)
    simulate_search_app("אלברט איינשטיין")
