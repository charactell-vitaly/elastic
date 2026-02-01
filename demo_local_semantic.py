import os
import wikipediaapi
import torch
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

# Initialize Elasticsearch client
if ELASTIC_CLOUD_ID:
    client = Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY)
else:
    client = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

# Use a local multilingual model
MODEL_NAME = "intfloat/multilingual-e5-small"
model = SentenceTransformer(MODEL_NAME)

INDEX_NAME = "local-multilingual-demo"

def create_index():
    if client.indices.exists(index=INDEX_NAME):
        print(f"Index {INDEX_NAME} already exists. Skipping creation.")
        return False
    
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "url": {"type": "keyword"},
                "category": {"type": "keyword"},
                "rating": {"type": "integer"},
                "content": {"type": "text"},
                "content_vector": {
                    "type": "dense_vector",
                    "dims": 384, # E5-small dimension
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
    client.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Created index: {INDEX_NAME}")
    return True

def fetch_data():
    print("Fetching Hebrew Wikipedia data...")
    wiki = wikipediaapi.Wikipedia(
        user_agent='ElasticSearchDemo/1.0',
        language='he'
    )
    # Define mapping of titles to categories and ratings
    wiki_items = {
        "ישראל": {"category": "Geography", "rating": 5},
        "ירושלים": {"category": "Geography", "rating": 4},
        "מדע": {"category": "Science", "rating": 5}
    }
    pages = []
    for t, meta in wiki_items.items():
        p = wiki.page(t)
        if p.exists():
            pages.append({
                "title": p.title, 
                "url": p.fullurl, 
                "content": p.summary,
                "category": meta["category"],
                "rating": meta["rating"]
            })
            print(f" - Fetched: {p.title} (Category: {meta['category']}, Rating: {meta['rating']})")
    return pages

def index_data(pages):
    print("Generating local embeddings and indexing...")
    actions = []
    for page in pages:
        # E5 models require 'passage: ' prefix for indexing
        vector = model.encode(f"passage: {page['content']}").tolist()
        actions.append({
            "_index": INDEX_NAME,
            "_source": {
                **page,
                "content_vector": vector
            }
        })
    helpers.bulk(client, actions)
    client.indices.refresh(index=INDEX_NAME)
    print("Success!")

def search(query_text):
    print(f"\nSearching for: '{query_text}'")
    # E5 models require 'query: ' prefix for searching
    query_vector = model.encode(f"query: {query_text}").tolist()
    
    response = client.search(
        index=INDEX_NAME,
        knn={
            "field": "content_vector",
            "query_vector": query_vector,
            "k": 3,
            "num_candidates": 10
        },
        _source=["title", "url"]
    )
    
    for hit in response["hits"]["hits"]:
        print(f" - {hit['_source']['title']} (Score: {hit['_score']:.4f})")

def main():
    # Check if we need to create and index
    if not client.indices.exists(index=INDEX_NAME):
        create_index()
        data = fetch_data()
        index_data(data)
    else:
        print(f"Index {INDEX_NAME} exists. Using existing data.")
    
    # Test queries
    search("History of Jewish people")
    search("מדינת ישראל")
    search("Modern science and research")

if __name__ == "__main__":
    main()
