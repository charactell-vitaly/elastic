from elasticsearch import Elasticsearch

es = Elasticsearch(
    'https://ee040075bc9e4bc29f645008831900d2.us-central1.gcp.cloud.es.io:443',
    api_key='TmMxTXdac0JsMndyUDZ1OEdsUUI6YmUzUUhyT1ZpUFIxOGRDdTBPUmoyQQ=='
)

# Check language distribution
agg = es.search(
    index='multilingual-scale-index',
    size=0,
    aggs={'langs': {'terms': {'field': 'language'}}}
)

print("=== Language Distribution ===")
for bucket in agg['aggregations']['langs']['buckets']:
    print(f"  {bucket['key']}: {bucket['doc_count']} docs")

# Check if Hebrew Einstein exists
print("\n=== Searching for Hebrew Einstein ===")
result = es.search(
    index='multilingual-scale-index',
    query={"match": {"title": "איינשטיין"}},
    size=5
)
print(f"Found {result['hits']['total']['value']} results")
for hit in result['hits']['hits']:
    print(f"  [{hit['_source']['language']}] {hit['_source']['title']}")

# Test semantic search
print("\n=== Semantic Search: 'Who is Albert Einstein?' (Top 20) ===")
semantic = es.search(
    index='multilingual-scale-index',
    query={"semantic": {"field": "content", "query": "Who is Albert Einstein?"}},
    size=20
)
for i, hit in enumerate(semantic['hits']['hits']):
    src = hit['_source']
    print(f"  {i+1}. [{src['language']}] {src['title']} (score: {hit['_score']:.2f})")
