"""Read-only access to the imported Nigeria facility registry."""
import gzip
import json
from functools import lru_cache

from .core import DATA


@lru_cache(maxsize=1)
def registry_data():
    with gzip.open(DATA / "data/facility_registry.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)


def search(state="", lga="", limit=100, verified_only=False):
    data = registry_data()
    rows = [facility for facility in data["facilities"]
            if (not state or facility["state"] == state)
                        and (not lga or facility["lga"] == lga)
                        and (not verified_only or (
                                facility["operation_status"] == "Operational"
                                and facility["registration_status"] == "Registered"
                                and facility["license_status"] == "Licensed"))]
    return {"source": data["source"], "disclaimer": data["disclaimer"],
            "total_matches": len(rows), "facilities": rows[:limit]}