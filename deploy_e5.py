import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()
es = Elasticsearch(os.getenv('ELASTIC_URL'), api_key=os.getenv('ELASTIC_API_KEY'), request_timeout=300)

MODEL_ID = ".multilingual-e5-small"

print(f"Deploying model: {MODEL_ID}...")
try:
    # Attempt to start the deployment
    res = es.ml.start_trained_model_deployment(model_id=MODEL_ID, wait_for="started")
    print(f"✅ Success! Model status: {res}")
except Exception as e:
    if "already started" in str(e).lower():
        print(f"ℹ️ Model {MODEL_ID} is already started.")
    else:
        print(f"❌ Failed to deploy model: {e}")
