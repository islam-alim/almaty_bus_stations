import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

place_name = "Almaty, Kazakhstan"

# road graph
G = ox.graph_from_place(place_name, network_type="drive")

# add speeds and travel times to use as the edges
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

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

start_stop = 109
end_stop = 9

# function returning the rote and time needed for this
def route_and_time(start, end):
    source = stops.iloc[start]["graph_node"]
    target = stops.iloc[end]["graph_node"]
    # dijkstra's algorithm
    route = nx.shortest_path(
        G,
        source=source,
        target=target,
        weight="travel_time"
    )
    # compute the time needed for the path
    travel_time_sec = nx.shortest_path_length(
        G,
        source,
        target,
        weight="travel_time"
    )
    return route, travel_time_sec

route, travel_time_sec = route_and_time(start_stop, end_stop)

# plot the shortest path
fig, ax = ox.plot_graph_route(
    G, route, route_linewidth=4, node_size=0, show=False, close=False, route_color="purple"
)

#fig, ax = ox.plot_graph(G, show=False, close=False)

# plot all stops
stops.plot(ax=ax, color="red", markersize=3)

# start stop
stops.iloc[[start_stop]].plot(ax=ax, color="green", markersize=50)

# end stop
stops.iloc[[end_stop]].plot(ax=ax, color="blue", markersize=50)

plt.show()

# print the stops of the route
node_to_name = dict(zip(stops["graph_node"], stops["name"]))
route_stop_names = [
    node_to_name[node]
    for node in route
    if node in node_to_name and pd.notna(node_to_name[node])
]
print("Route:", route_stop_names)

# time needed for the route
print("Travel time (minutes):", travel_time_sec / 60)

# for each stop we find the nearest node, so the number of nodes is also number of stops
print("General number of stops: ", len(nearest_nodes))

# list of stops
##stops_reset = stops.reset_index()
##print(stops_reset[["name"]].to_string())