import os
import json
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

if ELASTIC_CLOUD_ID:
    client = Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY)
else:
    client = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

def list_indices():
    print("--- Indices on your cluster ---")
    # Using 'cat' API for a concise list
    indices = client.cat.indices(format="json")
    for index in indices:
        # Filter out system indices for clarity
        if not index['index'].startswith('.'):
            print(f"Index: {index['index']} | Docs: {index['docs.count']} | Status: {index['status']}")

def show_sample_content(index_name):
    print(f"\n--- Sample content from '{index_name}' ---")
    try:
        res = client.search(index=index_name, size=1)
        if res['hits']['total']['value'] > 0:
            doc = res['hits']['hits'][0]['_source']
            print(json.dumps(doc, indent=2, ensure_ascii=False))
        else:
            print("Index is empty.")
    except Exception as e:
        print(f"Error reading {index_name}: {e}")

if __name__ == "__main__":
    list_indices()
    # Sample from both of our demo indices
    show_sample_content("local-multilingual-demo")
    show_sample_content("ct-multilingual-semantic-index")
