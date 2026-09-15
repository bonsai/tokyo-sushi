from aw.graph import run_aw


def test_price_query():
    result = run_aw("4000円くらいで初デート向きは？")
    assert result["query"]["min_price"] == 3000
    assert result["query"]["max_price"] == 5000
    assert len(result["stores"]) <= 12


def test_area_query():
    result = run_aw("新宿で4000円以下、会話しやすい寿司屋")
    assert result["query"]["area"] == "新宿"
    assert all(store["area"] == "新宿" for store in result["stores"])


def test_visual_weight():
    result = run_aw("3000〜5000円で見栄え重視")
    assert result["query"]["weights"]["visual"] > 0.15
