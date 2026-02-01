import os
import wikipediaapi
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers

# Load environment variables
load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

# Initialize Elasticsearch client
if ELASTIC_CLOUD_ID:
    client = Elasticsearch(
        cloud_id=ELASTIC_CLOUD_ID,
        api_key=ELASTIC_API_KEY,
        request_timeout=300
    )
else:
    client = Elasticsearch(
        ELASTIC_URL,
        api_key=ELASTIC_API_KEY,
        request_timeout=300
    )

INDEX_NAME = "ct-multilingual-semantic-index"
INFERENCE_ID = ".elser-2-elasticsearch"

def setup_inference():
    """Verify the inference service exists."""
    print(f"Verifying inference service: {INFERENCE_ID}")
    try:
        client.inference.get(inference_id=INFERENCE_ID)
        print("Inference service found and ready.")
    except Exception as e:
        print(f"Inference service check failed: {e}")
        print("Note: If this fails, the E5 model might still be initializing on the cluster nodes.")

def create_index():
    """Create an index with semantic_text mapping."""
    # Only create if it doesn't exist
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
                "content": {
                    "type": "semantic_text",
                    "inference_id": INFERENCE_ID
                }
            }
        }
    }
    client.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Created index: {INDEX_NAME} with semantic_text mapping.")
    return True

def fetch_wikipedia_pages():
    """Fetch 3 Hebrew Wikipedia pages for demonstration."""
    print("Fetching Wikipedia pages...")
    wiki = wikipediaapi.Wikipedia(
        user_agent='ElasticSearchSemanticDemo/1.0 (contact: user@example.com)',
        language='he'
    )
    
    wiki_items = {
        "ישראל": {"category": "Geography", "rating": 5},
        "ירושלים": {"category": "Geography", "rating": 4},
        "מדע": {"category": "Science", "rating": 5}
    }
    pages = []
    for title, meta in wiki_items.items():
        page = wiki.page(title)
        if page.exists():
            print(f" - Fetched: {page.title} (Category: {meta['category']}, Rating: {meta['rating']})")
            pages.append({
                "title": page.title,
                "url": page.fullurl,
                "content": page.summary,
                "category": meta["category"],
                "rating": meta["rating"]
            })
    return pages

def index_data(pages):
    """Index data into Elasticsearch."""
    print("Indexing data (this uses automatic chunking and embedding)...")
    actions = []
    for page in pages:
        actions.append({
            "_index": INDEX_NAME,
            "_source": {
                "title": page["title"],
                "url": page["url"],
                "content": page["content"],
                "category": page["category"],
                "rating": page["rating"]
            }
        })
    
    success, errors = helpers.bulk(client, actions, raise_on_error=False)
    if errors:
        print(f"Error: {len(errors)} document(s) failed to index.")
        for error in errors[:1]:
             print(f"Sample error: {error}")
    else:
        print(f"Successfully indexed {success} document.")
    
    client.indices.refresh(index=INDEX_NAME)

def search(query_text):
    """Perform semantic search."""
    print(f"\nSearching for [Semantic]: '{query_text}'")
    try:
        response = client.search(
            index=INDEX_NAME,
            query={
                "semantic": {
                    "field": "content",
                    "query": query_text
                }
            },
            _source=["title", "url"],
        )
        
        hits = response["hits"]["hits"]
        if not hits:
            print(" No results found.")
        for hit in hits:
            print(f" - {hit['_source']['title']} (Score: {hit['_score']:.4f})")
            print(f"   URL: {hit['_source']['url']}")
    except Exception as e:
        print(f"Search failed: {e}")

def main():
    try:
        info = client.info()
        print(f"Connected to Elasticsearch Version: {info['version']['number']}")
        
        setup_inference()
        
        # Check if we need to create and index
        if not client.indices.exists(index=INDEX_NAME):
            create_index()
            pages = fetch_wikipedia_pages()
            if pages:
                index_data(pages)
            else:
                print("No data fetched.")
        else:
            print(f"Index {INDEX_NAME} exists. Using existing data.")
            
        # Semantic search queries
        search("Jewish history and independent state")
        search("מדינות במזרח התיכון")
        search("Politics in Jerusalem")
        search("High tech and economy in Tel Aviv")
            
    except Exception as e:
        print(f"Runtime error: {e}")

if __name__ == "__main__":
    main()
