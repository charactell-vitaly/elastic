import os
import time
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

MODEL_ID = ".multilingual-e5-small"
INFERENCE_ID = "multilingual-e5-inference"

def reset():
    print(f"Step 1: Deleting inference service {INFERENCE_ID}...")
    try:
        client.inference.delete(inference_id=INFERENCE_ID)
        print("Done.")
    except Exception as e:
        print(f"Inference delete skipped/failed: {e}")

    print(f"Step 2: Stopping model deployment {MODEL_ID}...")
    try:
        client.ml.stop_trained_model_deployment(model_id=MODEL_ID, force=True)
        print("Done.")
        # Give it a moment to clear
        time.sleep(5)
    except Exception as e:
        print(f"Model stop skipped/failed: {e}")

    print(f"Step 3: Starting model deployment {MODEL_ID}...")
    try:
        client.ml.start_trained_model_deployment(
            model_id=MODEL_ID, 
            number_of_allocations=1, 
            wait_for="fully_allocated"
        )
        print("Model is fully allocated.")
    except Exception as e:
        print(f"Model start failed: {e}")
        return

    print(f"Step 4: Creating inference service {INFERENCE_ID}...")
    inference_config = {
        "service": "elasticsearch",
        "service_settings": {
            "num_allocations": 1,
            "num_threads": 1,
            "model_id": MODEL_ID
        }
    }
    try:
        client.inference.put(
            task_type="text_embedding",
            inference_id=INFERENCE_ID,
            body=inference_config
        )
        print("Inference service created.")
    except Exception as e:
        print(f"Inference creation failed: {e}")

if __name__ == "__main__":
    reset()
