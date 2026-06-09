from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx

app = Flask(__name__)

place_name = "Almaty, Kazakhstan"

print("Loading graph...")
G = ox.graph_from_place(
    place_name,
    network_type="drive",
    simplify=True
)
G = ox.project_graph(G)
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

print("Loading bus stops...")
stops = ox.features_from_place(place_name, tags={"highway": "bus_stop"})
stops = stops.to_crs(ox.graph_to_gdfs(G, nodes=False).crs)

# map stop index → nearest node
stop_nodes = []

for _, row in stops.iterrows():
    lon, lat = row.geometry.x, row.geometry.y
    node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
    stop_nodes.append(node)

stops["graph_node"] = stop_nodes


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

    return jsonify({
        "route": coords
    })


if __name__ == "__main__":
    app.run(debug=True)