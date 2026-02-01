import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

if ELASTIC_CLOUD_ID:
    client = Elasticsearch(
        cloud_id=ELASTIC_CLOUD_ID,
        api_key=ELASTIC_API_KEY,
        request_timeout=60
    )
else:
    client = Elasticsearch(
        ELASTIC_URL,
        api_key=ELASTIC_API_KEY,
        request_timeout=60
    )

INDEX_NAME = "test-semantic-index"
INFERENCE_ID = ".elser-2-elasticsearch"

def test():
    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
    
    mapping = {
        "mappings": {
            "properties": {
                "text": {
                    "type": "semantic_text",
                    "inference_id": INFERENCE_ID
                }
            }
        }
    }
    client.indices.create(index=INDEX_NAME, body=mapping)
    print("Index created.")
    
    print("Indexing English document...")
    try:
        client.index(index=INDEX_NAME, document={"text": "Hello, this is a test of semantic search using E5 multi-lingual model."}, refresh=True)
        print("Success!")
        
        print("Searching...")
        res = client.search(index=INDEX_NAME, query={"semantic": {"field": "text", "query": "greeting"}})
        print(f"Results: {res['hits']['total']['value']}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test()
