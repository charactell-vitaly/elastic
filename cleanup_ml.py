import os
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
    print("Checking for active ML model deployments...")
    stats = client.ml.get_trained_models_stats().body
    for model in stats.get('trained_model_stats', []):
        mid = model['model_id']
        if 'deployment_stats' in model:
            print(f"Found active deployment: {mid}")
            if mid != '.multilingual-e5-small':
                print(f"Stopping {mid} to free up capacity...")
                try:
                    client.ml.stop_trained_model_deployment(model_id=mid, force=True)
                    print(f"Successfully stopped {mid}")
                except Exception as e:
                    print(f"Error stopping {mid}: {e}")
            else:
                print(f"Skipping {mid} (we want this one)")

    print("\nCleanup complete.")
except Exception as e:
    print(f"Error during cleanup: {e}")
