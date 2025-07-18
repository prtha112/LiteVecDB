# LiteVecDB
LiteVecDB is a tiny local vector database. No server, no setup, no headache.

Just save vectors. Search them later. That’s it.

---

## 🔧 Install

```
pip install litevecdb  # not yet on PyPI, clone and use local for now
```

Or local dev:
```
git clone https://github.com/prtha112/LiteVecDB.git
cd LiteVecDB
pip install -e .
```

## 🚀 Quick Start
```python
from litevecdb import LiteVecDB

db = LiteVecDB(dim=3)
db.delete_all()

db.add([0.1, 0.2, 0.3], {"name": "apple", "category": "fruit"})
db.add([0.2, 0.2, 0.2], {"name": "banana", "category": "fruit"})
db.add([0.9, 0.8, 0.7], {"name": "tesla", "category": "car"})

query = [0.1, 0.2, 0.3]

# Only return items where category == "fruit"
results = db.search(query, k=5, filters={"category": "fruit"})

for score, meta in results:
    print(meta["name"])
# Output: apple, banana
```

## 🧠 Features
- Save vectors to disk in compressed shards
- Search by cosine similarity  
- Zero external dependencies (except numpy + zstd)
- Great for local RAG / prototyping
- Optional metadata filters (e.g. `{"category": "fruit"}`)

## 🛠 Test
```python
pytest tests/
```