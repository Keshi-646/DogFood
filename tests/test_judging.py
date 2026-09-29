def test_results_endpoint(client):
    r=client.get("/api/results")
    assert r.status_code==200
    assert isinstance(r.json,list)

def test_gallery_endpoint(client):
    r=client.get("/api/gallery")
    assert r.status_code==200
    assert len(r.json)>=1
