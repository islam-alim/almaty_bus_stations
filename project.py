import json
import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx

df = pd.read_csv("interpreter.csv", sep="\t")

G = nx.Graph()

for _, row in df.iterrows():

    if pd.isna(row["@lat"]) or pd.isna(row["@lon"]):
        continue

    G.add_node(
        row["@id"],
        pos=(row["@lon"], row["@lat"]),
        name=row["name"]
    )

pos = nx.get_node_attributes(G, "pos")


with open("export.json", "r", encoding="utf-8") as f:
    data = json.load(f)



osm_nodes = {}

for el in data["elements"]:
    if el["type"] == "node":
        osm_nodes[el["id"]] = (el["lon"], el["lat"])


plt.figure(figsize=(12, 12))



for el in data["elements"]:

    if el["type"] == "way":

        coords = []

        for nid in el["nodes"]:
            if nid in osm_nodes:
                coords.append(osm_nodes[nid])

        if len(coords) > 1:
            x = [c[0] for c in coords]
            y = [c[1] for c in coords]

            plt.plot(
                x,
                y,
                color="gray",
                linewidth=1
            )


nx.draw(
    G,
    pos=pos,
    node_size=10,
    node_color="blue",
    with_labels=False
)

plt.show()