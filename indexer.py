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

def fetch_wikipedia_pages(lang, count=100):
    """Fetch 'count' pages from Wikipedia in specific language."""
    wiki = wikipediaapi.Wikipedia(
        user_agent='ElasticSearchScaleDemo/1.0',
        language=lang
    )
    
    # PARALLEL TOPICS: Same subjects in all languages for relevance testing
    parallel_topics = {
        "History": ["Jerusalem", "World War II", "French Revolution", "Ancient Egypt", "Empire of Japan", "Ottoman Empire", "Renaissance", "Industrial Revolution", "Cold War", "Maya civilization"],
        "Science": ["Albert Einstein", "Climate change", "DNA", "Solar System", "Quantum mechanics", "Photosynthesis", "Black hole", "Evolution", "Periodic table", "General relativity"],
        "Technology": ["Artificial intelligence", "World Wide Web", "Blockchain", "SpaceX", "Nuclear power", "Smartphones", "Cloud computing", "Cryptography", "Internet of things", "Virtual reality"],
        "Geography": ["Mount Everest", "Amazon River", "Sahara", "Pacific Ocean", "Antarctica", "Great Barrier Reef", "Grand Canyon", "Alps", "Dead Sea", "Nile"],
        "Culture": ["Leonardo da Vinci", "William Shakespeare", "Ludwig van Beethoven", "Olympics", "Impressionism", "Jazz", "Socrates", "Gothic architecture", "Mythology", "Cinema"],
        "Space": ["Moon", "Mars", "Big Bang", "Galaxies", "International Space Station", "Black holes", "Hubble Space Telescope", "Astronaut", "Exoplanets", "Milky Way"],
        "Biology": ["Neurons", "Bacteria", "Viruses", "Human genome", "Heart", "Lungs", "Plant cells", "DNA replication", "Microbiology", "Ecosystem"],
        "Physics": ["Thermodynamics", "Electromagnetism", "Newton's laws of motion", "Gravity", "String theory", "Higgs boson", "Lightwaves", "Atomic nucleus", "Fluid dynamics", "Relativity"]
    }
    
    pages_to_fetch = []
    print(f"Gathering parallel topics for {lang}...")

    def process_title(english_title, category):
        try:
            en_wiki = wikipediaapi.Wikipedia(user_agent='ElasticSearchScaleDemo/1.0', language='en')
            en_page = en_wiki.page(english_title)
            
            target_title = english_title
            if lang != 'en' and en_page.exists():
                lang_links = en_page.langlinks
                if lang in lang_links:
                    target_title = lang_links[lang].title
            
            p = wiki.page(target_title)
            if p.exists():
                return {
                    "title": p.title,
                    "url": p.fullurl,
                    "content": p.summary[:5000].strip(),
                    "language": lang,
                    "category": category
                }
        except Exception:
            pass
        return None

    # Step 1: Process Parallel Topics in parallel
    topics_list = []
    for category, titles in parallel_topics.items():
        for t in titles:
            topics_list.append((t, category))

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda x: process_title(x[0], x[1]), topics_list))
        for res in results:
            if res and len(pages_to_fetch) < count:
                pages_to_fetch.append(res)
                print(f" - Fetched [{lang}]: {len(pages_to_fetch)} pages")

    # Step 2: Fill remaining with broad categories (Parallelized)
    if len(pages_to_fetch) < count:
        print(f"Filling remaining slots for {lang} using broad categories...")
        search_queries = {
            "en": ["Life", "World", "Society", "Thought", "Human", "Environment", "Language", "Mathematics", "Physical_sciences", "Applied_sciences", "Social_sciences", "Health", "Leisure", "Arts", "Biography", "History", "Geography", "Technology", "Science", "Politics"],
            "he": ["חיים", "עולם", "חברה", "מחשבה", "אדם", "סביבה", "שפה", "מתמטיקה", "מדעי_הטבע", "מדעים_יישומיים", "מדעי_החברה", "בריאות", "פנאי", "אמנות", "ביוגרפיה", "היסטוריה", "גאוגרפיה", "טכנולוגיה", "מדע", "פוליטיקה"],
            "ar": ["حياة", "علم", "مجتمع", "فكر", "إنسان", "بيئة", "لغة", "رياضيات", "علوم_طبيعية", "علوم_تطبيقية", "علوم_اجتماعية", "صحة", "ترفיה", "فنون", "سيرة_ذاتية", "تاريخ", "جغرافيا", "تكنولوجيا", "علوم", "سياسة"]
        }
        
        def get_category_members_recursive(cat, members_dict, depth=0, max_depth=1):
            if depth > max_depth: return
            try:
                # Limit to 500 per category to prevent infinite bloat
                for m in list(cat.categorymembers.values())[:500]:
                    if m.ns == wikipediaapi.Namespace.MAIN:
                        if m.title not in members_dict:
                            members_dict[m.title] = query
                    elif m.ns == wikipediaapi.Namespace.CATEGORY:
                        # Recursive call
                        get_category_members_recursive(m, members_dict, depth + 1, max_depth)
            except Exception:
                pass

        needed = count - len(pages_to_fetch)
        members_dict = {}
        for query in search_queries.get(lang, []):
            try:
                cat = wiki.page(f"Category:{query}")
                # Retry loop
                for _ in range(3):
                    try:
                        if cat.exists():
                            get_category_members_recursive(cat, members_dict, 0, 2) # Depth 2
                        break
                    except Exception:
                        time.sleep(1)
            except Exception:
                pass
            if len(members_dict) >= needed * 1.5: break

        category_pages = list(members_dict.items())[:needed*2]

        def fetch_basic(title, category):
            try:
                p = wiki.page(title)
                if p.exists():
                    return {
                        "title": p.title,
                        "url": p.fullurl,
                        "content": p.summary[:5000].strip(),
                        "language": lang,
                        "category": category
                    }
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=5) as executor: # Reduced workers
            cat_results = list(executor.map(lambda x: fetch_basic(x[0], x[1]), category_pages))
            for res in cat_results:
                if res and len(pages_to_fetch) < count:
                    if res['title'] not in [pg['title'] for pg in pages_to_fetch]:
                        pages_to_fetch.append(res)
                        if len(pages_to_fetch) % 10 == 0:
                            print(f" - Fetched [{lang}]: {len(pages_to_fetch)} pages")
    
    return pages_to_fetch[:count]

def main():
    es = get_es_client()
    setup_index(es)
    
    languages = ["en", "he", "ar"]
    all_pages = []
    
    for lang in languages:
        pages = fetch_wikipedia_pages(lang, count=500) # Aim for 500 per lang (1500 total)
        all_pages.extend(pages)
    
    print(f"Total pages to index: {len(all_pages)}")
    
    print("Performing bulk indexing...")
    actions = [
        {
            "_index": INDEX_NAME,
            "_source": page
        }
        for page in all_pages
    ]
    
    try:
        success, failed = helpers.bulk(es, actions, stats_only=False, chunk_size=10, raise_on_error=False)
        print(f"Successfully indexed {success} documents.")
        if failed:
            print(f"Failed to index {len(failed)} documents.")
            for i, error in enumerate(failed[:5]): # Show first 5 errors
                print(f" - Error {i+1}: {error}")
    except Exception as e:
        print(f"Critical error during bulk: {e}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Indexing completed in {time.time() - start_time:.2f} seconds.")
