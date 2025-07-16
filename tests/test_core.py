from litevecdb import LiteVecDB

def test_add_and_search():
    db = LiteVecDB(dim=3, dir_path="testdb")
    db.delete_all()
    db.add([1.0, 2.0, 3.0], {"text": "sample"})
    result = db.search([1.0, 2.0, 3.0])
    assert len(result) > 0
    assert result[0][1]["text"] == "sample"