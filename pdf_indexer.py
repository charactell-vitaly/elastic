import os
import fitz # PyMuPDF
from langdetect import detect
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv

load_dotenv()

# Elastic Config
ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
INDEX_NAME = "multilingual-scale-index"

def get_es_client():
    if ELASTIC_CLOUD_ID:
        return Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY, request_timeout=600)
    return Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY, request_timeout=600)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF and return content string. Return None if no text found."""
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        
        text = text.strip()
        return text if len(text) > 50 else None # Simple threshold for image-only PDFs
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def detect_language(text):
    """Detect language of text. Fallback to 'en'."""
    try:
        return detect(text)
    except:
        return "en"

def main():
    protocol_dir = r"D:\Users\vital\Download\Elastic-protocols\proptocols"
    if not os.path.exists(protocol_dir):
        print(f"Error: Directory not found: {protocol_dir}")
        return

    es = get_es_client()
    
    # Check if index exists (we don't want to re-setup, just append)
    if not es.indices.exists(index=INDEX_NAME):
        print(f"Error: Index {INDEX_NAME} not found. Please run indexer.py first.")
        return

    pdf_files = [f for f in os.listdir(protocol_dir) if f.lower().endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF files. Starting extraction...")

    actions = []
    for filename in pdf_files:
        path = os.path.join(protocol_dir, filename)
        content = extract_text_from_pdf(path)
        
        if content:
            lang = detect_language(content[:1000])
            doc = {
                "title": filename,
                "url": f"file:///{path.replace('\\', '/')}",
                "language": lang,
                "category": "Protocol",
                "content": content[:10000], # Limit content size for inference
                "original_title": filename
            }
            
            actions.append({
                "_index": INDEX_NAME,
                "_source": doc
            })
            print(f" + Prepared: {filename} (Lang: {lang})")
        else:
            print(f" - Skipped: {filename} (Likely image-only or corrupt)")

    if actions:
        print(f"\nIndexing {len(actions)} protocols to {INDEX_NAME}...")
        try:
            success, failed = helpers.bulk(es, actions, stats_only=False, chunk_size=5)
            print(f"Successfully indexed {success} documents.")
            if failed:
                print(f"Failed to index {len(failed)} documents.")
        except Exception as e:
            print(f"Critical error during bulk: {e}")
    else:
        print("No valid text documents found to index.")

if __name__ == "__main__":
    main()
