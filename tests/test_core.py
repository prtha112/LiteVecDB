from litevecdb import LiteVecDB

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