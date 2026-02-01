import os
import time
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
import wikipediaapi
import sys
from concurrent.futures import ThreadPoolExecutor

# Ensure UTF-8 output on Windows for Hebrew/Arabic characters
try:
    if sys.stdout.encoding != 'utf-8':
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Load environment variables
load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

INDEX_NAME = "multilingual-scale-index"
INFERENCE_ID = ".multilingual-e5-small-elasticsearch"  # Standard system ID

def get_es_client():
    if ELASTIC_CLOUD_ID:
        return Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY, request_timeout=600)
    return Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY, request_timeout=600)

def setup_index(es):
    """Create the index with semantic_text mapping."""
    if es.indices.exists(index=INDEX_NAME):
        print(f"Deleting existing index: {INDEX_NAME}")
        es.indices.delete(index=INDEX_NAME)

    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "url": {"type": "keyword"},
                "language": {"type": "keyword"},
                "category": {"type": "keyword"},
                "content": {
                    "type": "semantic_text",
                    "inference_id": INFERENCE_ID
                }
            }
        }
    }
    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Created index: {INDEX_NAME} with semantic_text")

def fetch_parallel_wikipedia_pages(languages=["en", "he", "ar"]):
    """Fetch parallel subjects across multiple languages to ensure ground truth."""
    wiki_clients = {lang: wikipediaapi.Wikipedia(user_agent='ScaleDemo/1.0', language=lang) for lang in languages}
    en_wiki = wiki_clients['en']
    
    # Core evaluation subjects (Ground Truth)
    subjects = [
        "Albert Einstein", "Jerusalem", "DNA", "Solar System", "Quantum mechanics",
        "Artificial intelligence", "World Wide Web", "Climate change", "Leonardo da Vinci",
        "William Shakespeare", "Olympics", "Ancient Egypt", "Empire of Japan", "French Revolution",
        "Black hole", "Evolution", "Photosynthesis", "Blockchain", "SpaceX", "Nuclear power",
        "Mount Everest", "Amazon River", "Sahara", "Pacific Ocean", "Antarctica",
        "Ludwig van Beethoven", "Socrates", "Gothic architecture", "Mythology", "Cinema",
        "Moon", "Mars", "Big Bang", "Galaxies", "International Space Station",
        "Bacteria", "Viruses", "Human genome", "Heart", "Ecosystem",
        "Thermodynamics", "Electromagnetism", "Gravity", "String theory", "Higgs boson"
    ]
    
    pages_to_index = []
    print(f"Starting parallel fetching for {len(subjects)} subjects across {languages}...")
    
    def get_parallel_for_subject(en_title):
        subject_pages = []
        # Robust retry logic for Wikipedia API
        for attempt in range(3):
            try:
                en_page = en_wiki.page(en_title)
                if not en_page.exists():
                    return None
                
                # Map of language to title for this subject
                lang_map = {'en': en_title}
                langlinks = en_page.langlinks
                for lang in languages:
                    if lang != 'en' and lang in langlinks:
                        lang_map[lang] = langlinks[lang].title
                
                # Fetch content for all available languages for this subject
                for lang, title in lang_map.items():
                    p = wiki_clients[lang].page(title)
                    if p.exists():
                        subject_pages.append({
                            "title": p.title,
                            "original_title": en_title, # Ground truth link
                            "url": p.fullurl,
                            "content": p.summary[:5000].strip(),
                            "language": lang,
                            "category": "Parallel Ground Truth"
                        })
                # Add a small delay between subjects to avoid rate limits
                time.sleep(0.5)
                return subject_pages
            except Exception as e:
                if attempt < 2:
                    print(f"Retry {attempt+1} for {en_title} due to: {e}")
                    time.sleep(2 * (attempt + 1))
                    continue
                else:
                    print(f"Failed {en_title} after 3 attempts: {e}")
                    return None
        return None

    with ThreadPoolExecutor(max_workers=5) as executor: # Reduced from 10
        results = list(executor.map(get_parallel_for_subject, subjects))
        for res in results:
            if res:
                pages_to_index.extend(res)
                print(f" - Progress: {len(pages_to_index)} pages gathered (Subject: {res[0]['original_title']})")
                
    return pages_to_index
    
    return pages_to_fetch[:count]

def main():
    es = get_es_client()
    setup_index(es)
    
    # 1. Parallel Ground Truth (Approx 130-150 pages)
    all_pages = fetch_parallel_wikipedia_pages(languages=["en", "he", "ar"])
    
    # 2. Add "Background Noise" (Approx 300 more pages)
    # We'll fetch random pages from these languages to fill the volume
    print("\nGathering background noise (random articles)...")
    wiki_en = wikipediaapi.Wikipedia(user_agent='ScaleDemo/1.0', language='en')
    wiki_he = wikipediaapi.Wikipedia(user_agent='ScaleDemo/1.0', language='he')
    wiki_ar = wikipediaapi.Wikipedia(user_agent='ScaleDemo/1.0', language='ar')
    
    def fetch_noise_batch(wiki, lang, count=50):
        noise = []
        # Use simple common words or broad categories
        seeds = ["Earth", "History", "Science", "Technology", "World", "Society"] if lang == 'en' else \
                ["כדור_הארץ", "היסטוריה", "מדע", "טכנולוגיה", "עולם", "חברה"] if lang == 'he' else \
                ["الأرض", "تاریخ", "علوم", "تكنولوجيا", "عالم", "مجتمع"]
        
        fetched = 0
        for seed in seeds:
            try:
                p = wiki.page(seed)
                if p.exists():
                    noise.append({
                        "title": p.title,
                        "url": p.fullurl,
                        "content": p.summary[:5000].strip(),
                        "language": lang,
                        "category": "Background Noise"
                    })
                    fetched += 1
                # Try sub-pages or links for more variety
                for link_title in list(p.links.keys())[:count]:
                    if fetched >= count: break
                    lp = wiki.page(link_title)
                    if lp.exists():
                        noise.append({
                            "title": lp.title,
                            "url": lp.fullurl,
                            "content": lp.summary[:5000].strip(),
                            "language": lang,
                            "category": "Background Noise"
                        })
                        fetched += 1
            except Exception:
                continue
            if fetched >= count: break
        return noise

    with ThreadPoolExecutor(max_workers=3) as executor:
        noise_results = list(executor.map(lambda x: fetch_noise_batch(x[0], x[1], 50), [(wiki_en, "en"), (wiki_he, "he"), (wiki_ar, "ar")]))
        for batch in noise_results:
            all_pages.extend(batch)
    
    print(f"\nTotal pages to index: {len(all_pages)}")
    
    print("Performing bulk indexing...")
    actions = [
        {
            "_index": INDEX_NAME,
            "_source": page
        }
        for page in all_pages
    ]
    
    try:
        # Use a small chunk size to avoid payload limits
        success, failed = helpers.bulk(es, actions, stats_only=False, chunk_size=10, raise_on_error=False)
        print(f"Successfully indexed {success} documents.")
        if failed:
            print(f"Failed to index {len(failed)} documents.")
    except Exception as e:
        print(f"Critical error during bulk: {e}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Indexing completed in {time.time() - start_time:.2f} seconds.")
