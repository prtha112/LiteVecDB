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

db.add([1.0, 2.0, 3.0], {"name": "item1"})
db.add([4.0, 5.0, 6.0], {"name": "item2"})

results = db.search([1.0, 2.0, 3.1], k=3)
print(results)
# Output: [{'vector': [1.0, 2.0, 3.0], 'metadata': {'name': 'item1'}, 'distance': 0.1}]
```

## 🧠 Features
- Save vectors to disk in compressed shards
- Search by cosine similarity  
- Zero external dependencies (except numpy + zstd)
- Great for local RAG / prototyping

## 🛠 Test
```python
pytest tests/
```