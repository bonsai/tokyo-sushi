import json
import re
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sushi.json"

DIMS = ["price", "visual", "conversation", "atmosphere", "surprise", "food"]
DEFAULT_WEIGHTS = {
    "price": 0.15,
    "visual": 0.15,
    "conversation": 0.20,
    "atmosphere": 0.20,
    "surprise": 0.10,
    "food": 0.20,
}


class State(TypedDict, total=False):
    question: str
    query: dict
    stores: list
    ranked: list
    result: dict


def load_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def parse_query(state: State) -> State:
    q = state["question"]
    query = {"min_price": None, "max_price": None, "target_price": None, "area": None, "limit": 12, "weights": DEFAULT_WEIGHTS.copy()}

    prices = [int(x.replace(",", "")) for x in re.findall(r"\d{1,3}(?:,\d{3})+|\d{3,5}", q)]
    if "まで" in q and prices:
        query["max_price"] = prices[0]
    elif len(prices) >= 2 and any(token in q for token in ["〜", "～", "-", "から"]):
        query["min_price"], query["max_price"] = prices[0], prices[1]
    elif prices:
        query["target_price"] = prices[0]
        query["min_price"] = max(0, prices[0] - 1000)
        query["max_price"] = prices[0] + 1000

    areas = ["新宿", "銀座", "丸の内", "渋谷", "恵比寿", "築地", "麻布十番", "秋葉原"]
    query["area"] = next((area for area in areas if area in q), None)

    keyword_weights = {
        "見栄え": "visual", "映え": "visual", "写真": "visual",
        "会話": "conversation", "話しやす": "conversation",
        "雰囲気": "atmosphere", "落ち着": "atmosphere",
        "サプライズ": "surprise", "驚": "surprise",
        "料理": "food", "味": "food", "美味": "food",
    }
    for keyword, dim in keyword_weights.items():
        if keyword in q:
            query["weights"][dim] += 0.10

    total = sum(query["weights"].values())
    query["weights"] = {k: round(v / total, 4) for k, v in query["weights"].items()}
    return {"query": query}


def retrieve(state: State) -> State:
    data = load_data()
    query = state["query"]
    stores = data["stores"]
    if query["min_price"] is not None:
        stores = [s for s in stores if s["price"] >= query["min_price"]]
    if query["max_price"] is not None:
        stores = [s for s in stores if s["price"] <= query["max_price"]]
    if query["area"]:
        area_stores = [s for s in stores if query["area"] in s.get("area", "")]
        if area_stores:
            stores = area_stores
    return {"stores": stores}


def rank(state: State) -> State:
    weights = state["query"]["weights"]
    ranked = []
    for store in state["stores"]:
        score = sum(store.get("scores", {}).get(dim, 0) * weight for dim, weight in weights.items())
        ranked.append({**store, "weighted_score": round(score, 4)})
    ranked.sort(key=lambda x: x["weighted_score"], reverse=True)
    return {"ranked": ranked[: state["query"]["limit"]]}


def emit(state: State) -> State:
    return {"result": {"query": state["query"], "count": len(state["ranked"]), "stores": state["ranked"]}}


graph = StateGraph(State)
graph.add_node("parse_query", parse_query)
graph.add_node("retrieve", retrieve)
graph.add_node("rank", rank)
graph.add_node("emit", emit)
graph.add_edge(START, "parse_query")
graph.add_edge("parse_query", "retrieve")
graph.add_edge("retrieve", "rank")
graph.add_edge("rank", "emit")
graph.add_edge("emit", END)
AW = graph.compile()


def run_aw(question: str) -> dict:
    return AW.invoke({"question": question})["result"]
