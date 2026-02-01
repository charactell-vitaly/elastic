import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

if ELASTIC_CLOUD_ID:
    es = Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY)
else:
    es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

INDEX_NAME = "multilingual-scale-index"

def diagnostic_search(query_text):
    print(f"\n--- PURE SEMANTIC for: '{query_text}' ---")
    body = {
        "query": {
            "semantic": {
                "field": "content",
                "query": query_text
            }
        },
        "size": 10
    }
    try:
        resp = es.search(index=INDEX_NAME, body=body)
        for i, hit in enumerate(resp['hits']['hits']):
            src = hit['_source']
            print(f"   Rank {i+1}: [{src['language']}] {src['title']} (Score: {hit['_score']})")
    except Exception as e:
        print(f"Error in pure semantic: {e}")

def hybrid_search(query_text):
    print(f"\n--- HYBRID (Semantic Content + Keyword Title) for: '{query_text}' ---")
    body = {
        "query": {
            "bool": {
                "should": [
                    {
                        "semantic": {
                            "field": "content",
                            "query": query_text,
                            "boost": 1.0
                        }
                    },
                    {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["title^10", "original_title^10"],
                            "type": "best_fields"
                        }
                    }
                ]
            }
        },
        "size": 10
    }
    try:
        resp = es.search(index=INDEX_NAME, body=body)
        for i, hit in enumerate(resp['hits']['hits']):
            src = hit['_source']
            print(f"   Rank {i+1}: [{src['language']}] {src['title']} (Score: {hit['_score']})")
    except Exception as e:
        print(f"Error in hybrid: {e}")

if __name__ == "__main__":
    diagnostic_search("Who is Albert Einstein?")
    hybrid_search("Who is Albert Einstein?")
    
    print("\n--- Testing Specific Hebrew Match ---")
    hybrid_search("אלברט איינשטיין")
