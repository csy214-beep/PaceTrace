import json
import os


def load_maps(maps_dir: str = None):
    if maps_dir is None:
        maps_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "maps"
        )
    items = []
    if not os.path.isdir(maps_dir):
        return items
    for f in sorted(os.listdir(maps_dir)):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(maps_dir, f), encoding="utf-8") as fh:
                data = json.load(fh)
            raw = data.get("mapData", [])
            pts = []
            for p in raw:
                lng, lat = p.split(",")
                pts.append([float(lat), float(lng)])
            if pts:
                items.append(
                    {
                        "id": data.get("mapId", f),
                        "name": data.get("mapName", f),
                        "coords": pts,
                    }
                )
        except Exception:
            pass
    return items
