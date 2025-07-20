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

results = db.search(query, k=5, filters={"category": "fruit"})

for score, meta, shard_id, index in results:
    print(f"{meta['name']} (score={score:.3f}, shard={shard_id}, index={index})")

# Output:
# apple (score=1.000, shard=0, index=0)
# banana (score=0.981, shard=0, index=1)
```

## ➕ Add vector with TTL
```python
import time

db = LiteVecDB(dim=3)

db.add(
    [0.1, 0.2, 0.3],
    {
        "name": "temporary vector",
        "expires_at": time.time() + 60  # Expires in 60 seconds
    }
)

db.add(
    [0.2, 0.3, 0.4],
    {
        "name": "permanent vector"
        # no expires_at → permanent
    }
)

db.purge_expired()

results = db.search([0.1, 0.2, 0.3])
# Only returns vectors that have not expired
# But not support purging in background yet
```

## ❌ Delete vectors
```python
results = db.search([0.1, 0.2, 0.3], k=1)
score, meta, shard_id, index = results[0]

db.delete(shard_id, index) # Deletes specific vector
db.delete_all()  # Deletes all vectors
```

## 🧠 Features
- ✅ Save vectors in compressed shards (Zstandard)
- ✅ Fast cosine similarity search (with NumPy)
- ✅ Optional metadata filters (e.g. {"category": "fruit"})
- ✅ TTL and expiration with purge_expired()
- ✅ Get vector location: shard ID + index (great for precise deletes)
- ✅ Lightweight: only depends on numpy and zstandard
- ✅ Ideal for local RAG pipelines or prototyping

## 🛠 Test
```python
pytest tests/
```