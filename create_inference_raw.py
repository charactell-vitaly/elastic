import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")

# Create Inference Service using raw REST API
inference_id = "multilingual-e5-inference"
url = f"{ELASTIC_URL}/_inference/text_embedding/{inference_id}"

headers = {
    "Authorization": f"ApiKey {ELASTIC_API_KEY}",
    "Content-Type": "application/json"
}

body = {
    "service": "elasticsearch",
    "service_settings": {
        "num_allocations": 1,
        "num_threads": 1,
        "model_id": ".multilingual-e5-small"
    }
}

print(f"Sending PUT request to {url}...")
try:
    response = requests.put(url, headers=headers, json=body)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
