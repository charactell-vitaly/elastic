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

try:
    print("Listing all trained models...")
    models = client.ml.get_trained_models().body
    for model in models.get('trained_model_configs', []):
        print(f"Model ID: {model['model_id']}")
        print(f"  Description: {model.get('description', 'N/A')}")
        print("-" * 20)
    
    print("\nChecking deployment stats...")
    stats = client.ml.get_trained_models_stats().body
    print(json.dumps(stats, indent=2))

except Exception as e:
    print(f"Error: {e}")
