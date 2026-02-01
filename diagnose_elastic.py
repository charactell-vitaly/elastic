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
    print("Listing inference services...")
    # This might fail if the inference API is not supported or has different syntax
    try:
        services = client.inference.get()
        print(json.dumps(services.body, indent=2))
    except Exception as e:
        print(f"Error listing inference services: {e}")

    print("\nChecking cluster info...")
    print(json.dumps(client.info().body, indent=2))

except Exception as e:
    print(f"Error: {e}")
