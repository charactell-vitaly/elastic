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

def check_remote_einstein():
    print(f"--- Checking Remote Index: {INDEX_NAME} ---")
    
    # 1. Total count
    count = es.count(index=INDEX_NAME)['count']
    print(f"Total documents: {count}")
    
    # 2. Check for Hebrew Einstein specifically
    print("\n--- Searching for 'אלברט איינשטיין' (Keyword) ---")
    res = es.search(
        index=INDEX_NAME,
        query={"match": {"title": "אלברט איינשטיין"}},
        size=5
    )
    print(f"Found: {res['hits']['total']['value']} documents")
    for hit in res['hits']['hits']:
        src = hit['_source']
        print(f"  Title: {src['title']}")
        print(f"  Lang: {src['language']}")
        print(f"  Content length: {len(src['content'])}")
        # Check if inference worked (content semantic text)
        print(f"  Has Inference? {'semantic_text' in hit['fields'] if 'fields' in hit else 'Uncertain'}")

    # 3. Aggregation by language
    print("\n--- Language Distribution ---")
    agg = es.search(
        index=INDEX_NAME,
        size=0,
        aggs={"langs": {"terms": {"field": "language"}}}
    )
    for b in agg['aggregations']['langs']['buckets']:
        print(f"  {b['key']}: {b['doc_count']}")

if __name__ == "__main__":
    check_remote_einstein()
