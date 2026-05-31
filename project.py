import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

place_name = "Almaty, Kazakhstan"

# road graph
G = ox.graph_from_place(place_name, network_type="drive")

# bus stops
stops = ox.features_from_place(
    place_name,
    tags={"highway": "bus_stop"}
)

# make sure CRS matches graph CRS
stops = stops.to_crs(ox.graph_to_gdfs(G, nodes=False).crs)

# store nearest graph node for each stop
nearest_nodes = []

for idx, row in stops.iterrows():

    # point geometry
    point = row.geometry

    lon = point.x
    lat = point.y

    # nearest node in road graph
    nearest = ox.distance.nearest_nodes(G, X=lon, Y=lat)

    nearest_nodes.append(nearest)

# add node ids into dataframe
stops["graph_node"] = nearest_nodes

print(stops[["name", "graph_node"]].head())


source = stops.iloc[0]["graph_node"]
target = stops.iloc[5]["graph_node"]

route = nx.shortest_path(
    G,
    source=source,
    target=target,
    weight="length"
)

print(route)

fig, ax = ox.plot_graph(G, show=False, close=False)
stops.plot(ax=ax, color="red", markersize=3)
plt.show()