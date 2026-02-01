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

def test_filtered_semantic(query_text, lang_filter):
    print(f"\n--- Testing Filtered Semantic: Query='{query_text}', Lang='{lang_filter}' ---")
    
    search_query = {
        "semantic": {
            "field": "content",
            "query": query_text
        }
    }
    
    body = {
        "query": {
            "bool": {
                "must": [search_query],
                "filter": [{"term": {"language": lang_filter}}]
            }
        },
        "size": 10
    }
    
    resp = es.search(index=INDEX_NAME, body=body)
    print(f"Total hits: {resp['hits']['total']['value']}")
    for i, hit in enumerate(resp['hits']['hits']):
        src = hit['_source']
        print(f"  {i+1}. [{src['language']}] {src['title']} (Score: {hit['_score']})")

if __name__ == "__main__":
    test_filtered_semantic("Einstein", "he")
    test_filtered_semantic("Albert Einstein", "he")
    test_filtered_semantic("Albert Einstein", "ar")
