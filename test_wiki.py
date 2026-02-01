import wikipediaapi
import sys

# Ensure UTF-8 output
try:
    if sys.stdout.encoding != 'utf-8':
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def test_fetch(lang, title):
    print(f"Testing fetch [{lang}]: {title}")
    wiki = wikipediaapi.Wikipedia(
        user_agent='ElasticSearchScaleDemo/1.0',
        language=lang
    )
    p = wiki.page(title)
    if p.exists():
        print(f"✅ Success: {p.title} (Summary length: {len(p.summary)})")
    else:
        print(f"❌ Failed: Page does not exist.")

if __name__ == "__main__":
    test_fetch('en', 'Albert Einstein')
    test_fetch('he', 'אלברט איינשטיין')
    test_fetch('ar', 'ألبرت أينشتاين')
