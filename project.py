import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

place_name = "Almaty, Kazakhstan"

# get the road map
G = ox.graph_from_place(place_name, network_type="drive")

#G = ox.project_graph(G)

# get the bus_stop edges
stops = ox.features_from_place(place_name, tags={"highway": "bus_stop"})


# plot the graph
fig, ax = ox.plot_graph(G, show=False, close=False)

#plot the bus stops
stops.plot(ax=ax, color="red", markersize=10)

plt.show()
