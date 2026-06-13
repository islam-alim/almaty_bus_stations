from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
import json
import os
import geopandas as gpd
import pickle

app = Flask(__name__)

place_name = "Almaty, Kazakhstan"

print("Loading graph...")
G = ox.load_graphml("almaty.graphml")

print("Loading bus stops...")
stops = gpd.read_file("stops.geojson")

# load the route_stops
print("Loading route_stops...")
with open("route_stops.pkl", "rb") as f:
    route_stops = pickle.load(f)
print("Loaded routes:", len(route_stops))

# map stop index → nearest node
stop_nodes = []

for _, row in stops.iterrows():
    lon, lat = row.geometry.x, row.geometry.y
    node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
    stop_nodes.append(node)

stops["graph_node"] = stop_nodes

# adding bus routes

ROUTE_DIR = "routes"

#def route_nodes():
#    route_nodes = {}

  #  for file in os.listdir("routes"):
  #      if not file.endswith(".json"):
 #           continue
#
 #       route_id = os.path.splitext(file)[0]
#
  #      with open(os.path.join("routes", file), encoding="utf-8") as f:
 #           data = json.load(f)
#
 #       nodes = set()

  #      for direction in data:
  #          for lat, lon in direction["line"]:
 #               node = ox.distance.nearest_nodes(
#                    G, X=lon, Y=lat
  #              )
 #               nodes.add(node)
#
 #       route_nodes[route_id] = nodes
#
 #   return route_nodes
#
#def busses_for_path(path, route_nodes):
#
#    buses = set()
#
#    path_set = set(path)
#
#    for route_id, nodes in route_nodes.items():
#        if path_set.intersection(nodes):
#           buses.add(route_id)
#    return sorted(buses)

def buses_for_stop(stop_id):

    buses = []

    for route_id, stop_list in route_stops.items():

        if stop_id in stop_list:
            buses.append(route_id)

    return buses

@app.route("/routes/all")
def all_routes():

    routes = []

    for file in os.listdir(ROUTE_DIR):

        # skip non-json files
        if not file.endswith(".json"):
            continue

        path = os.path.join(ROUTE_DIR, file)

        # skip empty files
        if os.path.getsize(path) == 0:
            print("Skipping empty file:", file)
            continue

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            routes.append({
                "routeId": file.replace(".json", ""),
                "directions": data
            })

        except json.JSONDecodeError:
            print("Skipping broken JSON:", file)

    return jsonify(routes)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stops")
def get_stops():
    data = []
    for idx, (_, row) in enumerate(stops.iterrows()):
        data.append({
            "id": idx,
            "lat": row.geometry.y,
            "lon": row.geometry.x,
            "name": str(row.get("name", "Bus stop"))
        })
    return jsonify(data)


@app.route("/route", methods=["POST"])
def route():
    data = request.json
    start = int(data["start"])
    end = int(data["end"])

    source = stops.iloc[start]["graph_node"]
    target = stops.iloc[end]["graph_node"]

    route = nx.shortest_path(G, source, target, weight="travel_time")

    coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]

  #  buses = busses_for_path(route, route_nodes())
    start_buses = buses_for_stop(start)
    end_buses = buses_for_stop(end)

    direct_buses = list(set(start_buses) & set(end_buses))

    return jsonify({
        "route": coords,
        "buses": direct_buses
      #  "buses": buses
    })

@app.route("/test/<int:stop_id>")
def test(stop_id):

    return jsonify({
        "stop": stop_id,
        "buses": buses_for_stop(stop_id)
    })

if __name__ == "__main__":
    app.run(debug=True)