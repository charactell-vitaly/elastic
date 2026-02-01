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
    # Using a more descriptive User-Agent as per Wikipedia policy
    ua = 'MultilingualSemanticSearchDemo/1.0 (https://github.com/charactell-vitaly/elastic; contact: vitaly@example.com)'
    wiki_clients = {lang: wikipediaapi.Wikipedia(user_agent=ua, language=lang) for lang in languages}
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
    print(f"Starting sequential parallel fetching for {len(subjects)} subjects across {languages}...")
    
    for en_title in subjects:
        # Exponential backoff retry logic
        success = False
        for attempt in range(4):
            try:
                en_page = en_wiki.page(en_title)
                if not en_page.exists():
                    print(f" ! English subject '{en_title}' does not exist. Skipping.")
                    break
                
                # Map of language to title for this subject
                lang_map = {'en': en_title}
                langlinks = en_page.langlinks
                for lang in languages:
                    if lang != 'en' and lang in langlinks:
                        lang_map[lang] = langlinks[lang].title
                
                subject_pages = []
                # Fetch content for all available languages for this subject
                for lang, title in lang_map.items():
                    p = wiki_clients[lang].page(title)
                    if p.exists():
                        subject_pages.append({
                            "title": p.title,
                            "original_title": en_title,
                            "url": p.fullurl,
                            "content": p.summary[:5000].strip(),
                            "language": lang,
                            "category": "Parallel Ground Truth"
                        })
                    time.sleep(0.2) # Throttling within subject
                
                pages_to_index.extend(subject_pages)
                print(f" + Gathered: {en_title} ({len(subject_pages)} languages)")
                success = True
                break
            except Exception as e:
                wait_time = (2 ** attempt) + 1
                if attempt < 3:
                    print(f" ? Rate limit/error for '{en_title}' (Attempt {attempt+1}). Retrying in {wait_time}s... Error: {e}")
                    time.sleep(wait_time)
                else:
                    print(f" x Failed '{en_title}' after multiple attempts. Error: {e}")
        
        # Consistent delay between different subjects
        time.sleep(0.5)
                
    return pages_to_index
    
    return pages_to_fetch[:count]

def main():
    es = get_es_client()
    setup_index(es)
    
    # 1. Parallel Ground Truth (Approx 130-150 pages)
    all_pages = fetch_parallel_wikipedia_pages(languages=["en", "he", "ar"])
    
    # 2. Add "Background Noise" (Approx 150-200 more pages)
    print("\nGathering background noise (random articles)...")
    ua = 'MultilingualSemanticSearchDemo/1.0 (https://github.com/charactell-vitaly/elastic; contact: vitaly@example.com)'
    wiki_en = wikipediaapi.Wikipedia(user_agent=ua, language='en')
    wiki_he = wikipediaapi.Wikipedia(user_agent=ua, language='he')
    wiki_ar = wikipediaapi.Wikipedia(user_agent=ua, language='ar')
    
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
                    time.sleep(0.3) # Throttling within link iteration
            except Exception:
                continue
            if fetched >= count: break
            time.sleep(0.5) # Throttling between seeds
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
