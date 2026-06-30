import osmnx as ox

place_name = "Almaty, Kazakhstan"

print("Building graph...")

G = ox.graph_from_place(
    place_name,
    network_type="drive"
)

G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

ox.save_graphml(G, "almaty.graphml")

print("Graph is saved!")

print("Building stops...")

stops = ox.features_from_place(place_name, tags={"highway": "bus_stop"})
stops = stops.to_crs(ox.graph_to_gdfs(G, nodes=False).crs)

stops.to_file("stops.geojson", driver="GeoJSON")

print("Stops are saved!")