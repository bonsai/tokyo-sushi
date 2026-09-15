from pathlib import Path
import json
import math

import matplotlib.pyplot as plt
import contextily as ctx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sushi.json"
OUTPUT = ROOT / "static" / "map.png"
MAX_STORES = 12


def load_stores():
    with DATA.open("r", encoding="utf-8") as f:
        data = json.load(f)

    stores = data.get("stores", []) if isinstance(data, dict) else data
    return [
        store for store in stores
        if store.get("lat") is not None and store.get("lng") is not None
    ][:MAX_STORES]


def mercator(lon, lat):
    lat = max(-85.05112878, min(85.05112878, lat))
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y *= 20037508.34 / 180
    return x, y


def main():
    stores = load_stores()
    if not stores:
        raise RuntimeError("lat/lng を持つ店舗がありません")

    points = [mercator(float(s["lng"]), float(s["lat"])) for s in stores]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    fig, ax = plt.subplots(figsize=(12, 9))
    margin_x = (max(xs) - min(xs)) * 0.15 or 5000
    margin_y = (max(ys) - min(ys)) * 0.15 or 5000
    ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
    ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom="auto")

    ax.scatter(xs, ys, s=180, marker="o", edgecolors="white", linewidths=2, zorder=10)

    for i, (store, x, y) in enumerate(zip(stores, xs, ys), 1):
        name = store.get("name", f"Store {i}")
        ax.annotate(
            f"{i}. {name}",
            (x, y),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.85, edgecolor="none"),
            zorder=11,
        )

    ax.set_axis_off()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=180, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"generated: {OUTPUT} ({len(stores)} stores)")


if __name__ == "__main__":
    main()
