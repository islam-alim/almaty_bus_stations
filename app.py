from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
import json
import os
import geopandas as gpd
import pickle
import pandas as pd
from itertools import islice

app = Flask(__name__)

place_name = "Almaty, Kazakhstan"
BUS_EDGE_WEIGHT = 20
WALK_WEIGHT_PER_METER = 12
WALK_EDGE_PENALTY = 200
DISPLAY_ROUTE_COUNT = 3
CANDIDATE_ROUTE_COUNT = 30

print("Loading graph...")
G = ox.load_graphml("almaty.graphml")

print("Loading bus stops...")
stops = gpd.read_file("stops.geojson")

# load the route_stops
print("Loading route_stops...")
with open("route_stops.pkl", "rb") as f:
    route_stops = pickle.load(f)
print("Loaded routes:", len(route_stops))

# create transit_graph
G_transit = nx.MultiDiGraph()

# copy all road edges
for u, v, data in G.edges(data=True):
    length = data.get("length", 1)
    G_transit.add_edge(
        u,
        v,
        weight=(length * WALK_WEIGHT_PER_METER) + WALK_EDGE_PENALTY,
        mode="walk"
    )

# map stop index → nearest node
stop_nodes = ox.distance.nearest_nodes(
    G,
    X=stops.geometry.x,
    Y=stops.geometry.y
)

stops["graph_node"] = stop_nodes

# add bus edges between consecutive stops for each route
for route_id, stop_ids in route_stops.items():
    for i in range(len(stop_ids) - 1):
        from_stop = stop_ids[i]
        to_stop = stop_ids[i + 1]

        if from_stop == to_stop:
            continue

        G_transit.add_edge(
            stops.iloc[from_stop]["graph_node"],
            stops.iloc[to_stop]["graph_node"],
            weight=BUS_EDGE_WEIGHT,
            mode="bus",
            route=route_id
        )

G_route = nx.DiGraph()

for u, v, data in G_transit.edges(data=True):
    weight = data.get("weight", 1)

    if not G_route.has_edge(u, v) or weight < G_route[u][v].get("weight", 1):
        G_route.add_edge(u, v, weight=weight)

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

def stop_display_name(row, index):
    for field in ("name:en", "int_name", "name", "name:ru", "name:kk"):
        value = row.get(field)

        if value is not None and not pd.isna(value) and str(value).strip():
            return str(value)

    return f"Bus stop {index}"

def route_details(path):
    coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]
    instructions = []
    total_weight = 0

    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]

        edge_data = G_transit.get_edge_data(u, v)

        # NetworkX uses the minimum edge weight between parallel MultiDiGraph edges.
        edge = min(edge_data.values(), key=lambda item: item.get("weight", 1))
        total_weight += edge.get("weight", 1)

        instructions.append({
            "mode": edge.get("mode"),
            "route": edge.get("route")
        })

    buses = sorted({
        instruction["route"]
        for instruction in instructions
        if instruction.get("mode") == "bus" and instruction.get("route")
    })

    return {
        "route": coords,
        "instructions": instructions,
        "buses": buses,
        "transfers": count_bus_transfers(instructions),
        "walking_connections": count_walking_connections(instructions),
        "weight": total_weight
    }

def count_bus_transfers(instructions):
    transfers = 0
    current_route = None

    for instruction in instructions:
        if instruction.get("mode") != "bus" or not instruction.get("route"):
            continue

        route = instruction["route"]

        if current_route is not None and route != current_route:
            transfers += 1

        current_route = route

    return transfers

def count_walking_connections(instructions):
    connections = 0

    for index in range(1, len(instructions)):
        previous = instructions[index - 1]
        current = instructions[index]

        if previous.get("mode") != current.get("mode"):
            connections += 1

    return connections

def route_sort_key(route):
    return (
        route["transfers"],
        route["walking_connections"],
        route["weight"]
    )

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
            "name": stop_display_name(row, idx)
        })
    return jsonify(data)


@app.route("/route", methods=["POST"])
def route():
    data = request.json
    start = int(data["start"])
    end = int(data["end"])

    source = stops.iloc[start]["graph_node"]
    target = stops.iloc[end]["graph_node"]

    try:
        paths = list(islice(
            nx.shortest_simple_paths(G_route, source, target, weight="weight"),
            CANDIDATE_ROUTE_COUNT
        ))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        paths = []

    routes = sorted(
        (route_details(path) for path in paths),
        key=route_sort_key
    )[:DISPLAY_ROUTE_COUNT]

    if not routes:
        return jsonify({
            "route": [],
            "instructions": [],
            "routes": []
        })

    best_route = routes[0]

    return jsonify({
        "route": best_route["route"],
        "instructions": best_route["instructions"],
        "buses": best_route["buses"],
        "routes": routes
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
