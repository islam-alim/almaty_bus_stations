import os
import json
import pickle
import geopandas as gpd


ROUTE_DIR = "routes"

print("Loading stops...")

stops = gpd.read_file("stops.geojson")
stops = stops.reset_index(drop=True)

print("Stops loaded:", len(stops))

stop_points = []

for idx, row in stops.iterrows():

    stop_points.append({
        "id": idx,
        "lat": row.geometry.y,
        "lon": row.geometry.x
    })

def nearest_stop(lat, lon):

    best_stop = None
    best_dist = float("inf")

    for stop in stop_points:

        dist = ((stop["lat"] - lat) ** 2 + (stop["lon"] - lon) ** 2)

        if dist < best_dist:
            best_dist = dist
            best_stop = stop["id"]

    return best_stop

route_stops = {}

files = [f for f in os.listdir(ROUTE_DIR) if f.endswith(".json")]

print("Route files:", len(files))

for file in files:

    route_id = os.path.splitext(file)[0]

    print("Processing", route_id)

    with open(
        os.path.join(ROUTE_DIR, file),
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    stops_for_route = []

    for direction in data:

        line = direction["line"]

        for lat, lon in line:

            stop_id = nearest_stop(lat, lon)

            if (
                len(stops_for_route) == 0
                or stops_for_route[-1] != stop_id
            ):
                stops_for_route.append(stop_id)
    route_stops[route_id] = stops_for_route

with open("route_stops.pkl", "wb") as f:
    pickle.dump(route_stops, f)

print("Saved route_stops.pkl")