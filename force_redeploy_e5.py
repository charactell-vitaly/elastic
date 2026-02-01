import os
import time
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()
es = Elasticsearch(os.getenv('ELASTIC_URL'), api_key=os.getenv('ELASTIC_API_KEY'), request_timeout=300)

MODEL_ID = ".multilingual-e5-small"

print(f"Force-stopping deployment: {MODEL_ID}...")
try:
    es.ml.stop_trained_model_deployment(model_id=MODEL_ID, force=True)
    print("Stopped.")
except Exception as e:
    print(f"Error stopping (may not be running): {e}")

time.sleep(5)

print(f"Re-deploying model: {MODEL_ID}...")
try:
    res = es.ml.start_trained_model_deployment(model_id=MODEL_ID, wait_for="started")
    print(f"✅ Success! Model status: {res}")
except Exception as e:
    print(f"❌ Failed to deploy model: {e}")
