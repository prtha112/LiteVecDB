from litevecdb import LiteVecDB
import time

def test_add_and_search():
    db = LiteVecDB(dim=3, dir_path="testdb")
    db.delete_all()
    db.add([1.0, 2.0, 3.0], {"text": "sample"})
    result = db.search([1.0, 2.0, 3.0])
    assert len(result) > 0
    assert result[0][1]["text"] == "sample"

def test_search_with_filter():
    db = LiteVecDB(dim=3, dir_path="testdb")
    db.delete_all()
    db.add([1.0, 2.0, 3.0], {"text": "sample", "location": "Bangkok"})
    db.add([1.0, 1.0, 1.0], {"text": "sample2", "location": "Chiang Mai"})
    result = db.search([1.0, 2.0, 3.0], k=3, filters={"location": "Bangkok"})
    assert len(result) > 0
    assert result[0][1]["text"] == "sample"

def test_search_expired_entries():
    db = LiteVecDB(dim=3, dir_path="testdb")
    db.delete_all()
    db.add([1.0, 2.0, 3.0], {"text": "sample", "location": "Bangkok"})
    db.add([1.0, 1.0, 1.0], {"text": "sample2", "location": "Bangkok", "expires_at": time.time() + 1})
    db.purge_expired()
    # Wait for a moment to ensure the expiration is processed
    time.sleep(2)
    result = db.search([1.0, 2.0, 3.0], k=3, filters={"location": "Bangkok"})
    assert len(result) > 0
    assert result[0][1]["text"] == "sample"

def test_search_with_shard_and_index():
    db = LiteVecDB(dim=3, dir_path="testdb")
    db.delete_all()
    for i in range(10):
        vec = [1.0 * i, 2.0, 3.0]
        db.add(vec, {"text": f"item-{i}"})
    
    query = [9.0, 2.0, 3.0]
    result = db.search(query, k=3)

    assert len(result) == 3
    for score, meta, shard_id, index in result:
        assert isinstance(score, float)
        assert isinstance(meta, dict)
        assert isinstance(shard_id, int)
        assert isinstance(index, int)
        shard = db._load_shard(shard_id)
        assert meta == shard['metadata'][index]

def test_delete_single_vector():
    db = LiteVecDB(dim=3, dir_path="testdb")
    db.delete_all()

    db.add([1.0, 2.0, 3.0], {"text": "sample1"})
    db.add([4.0, 5.0, 6.0], {"text": "sample2"})

    all_data = db.get_all()
    assert len(all_data) == 2

    db.delete(shard_id=0, index=0)

    remaining = db.get_all()
    assert len(remaining) == 1
    assert remaining[0]["metadata"]["text"] == "sample2"

def test_delete_all_data():
    db = LiteVecDB(dim=3, dir_path="testdb")
    db.delete_all()

    db.add([1.0, 2.0, 3.0], {"text": "sample1"})
    db.add([4.0, 5.0, 6.0], {"text": "sample2"})

    assert len(db.get_all()) == 2

    db.delete_all()

    assert db.get_all() == []
    assert db.shard_index["counts"] == {}
    assert db.shard_index["last_shard"] == 0