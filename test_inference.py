import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()
es = Elasticsearch(os.getenv('ELASTIC_URL'), api_key=os.getenv('ELASTIC_API_KEY'))

endpoints = ["multilingual-e5-inference", "e5-small", ".multilingual-e5-small-elasticsearch"]

for eid in endpoints:
    print(f"\nTesting Inference ID: {eid}")
    try:
        res = es.inference.inference(inference_id=eid, body={"input": ["Hello world"]})
        print(f"✅ Success! (Embedding length: {len(res.body['text_embedding'][0]['embedding'])})")
    except Exception as e:
        print(f"❌ Failed: {e}")
