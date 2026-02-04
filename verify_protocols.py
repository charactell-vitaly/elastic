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

def verify():
    # Search specifically for Protocol category
    print("--- Searching for Category: Protocol ---")
    res = es.search(
        index=INDEX_NAME,
        query={"term": {"category": "Protocol"}},
        size=10
    )
    
    print(f"Total Protocols found: {res['hits']['total']['value']}")
    for hit in res['hits']['hits']:
        src = hit['_source']
        print(f"  - [{src['language']}] {src['title']} (Snippet: {src['content'][:100]}...)")

if __name__ == "__main__":
    verify()
