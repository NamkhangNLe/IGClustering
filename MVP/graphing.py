import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# Load the data from Merged.csv
df = pd.read_csv('Merged.csv')

# Create a new undirected graph
G = nx.Graph()

# Add a node for yourself
G.add_node('Your Name')

# Add a node for each person in the DataFrame and an edge from you to them
for index, row in df.iterrows():
    G.add_node(row['full_name'])
    G.add_edge('Your Name', row['full_name'])

# Draw the graph
pos = nx.spring_layout(G)  # positions for all nodes

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_color='red', node_size=10)

# Draw edges
nx.draw_networkx_edges(G, pos, edge_color='k', width=0.1)

plt.show()