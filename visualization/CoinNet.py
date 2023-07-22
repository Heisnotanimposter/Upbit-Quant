#!/usr/bin/env python
# coding: utf-8

# In[3]:
#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# Sample data (replace this with your actual DataFrame)
data = {
    'A': [1.0, 0.2, -0.3, 0.8],
    'B': [0.2, 1.0, 0.7, -0.4],
    'C': [-0.3, 0.7, 1.0, 0.1],
    'D': [0.8, -0.4, 0.1, 1.0]
}
df = pd.DataFrame(data)

corr_matrix = df.corr()

# Create a new graph
G = nx.Graph()

# Add nodes
for symbol in corr_matrix.columns:
    G.add_node(symbol)

# Add edges
for i in range(corr_matrix.shape[0]):
    for j in range(i+1, corr_matrix.shape[1]):
        symbol1 = corr_matrix.columns[i]
        symbol2 = corr_matrix.columns[j]
        correlation = corr_matrix.iloc[i, j]
        if not np.isnan(correlation):
            G.add_edge(symbol1, symbol2, weight=correlation)

# Draw the graph
plt.figure(figsize=(10, 10))
pos = nx.spring_layout(G)  # positions for all nodes

# Separate positive and negative correlations
pos_corr_edges = [(u, v) for u, v, d in G.edges(data=True) if d['weight'] > 0]
neg_corr_edges = [(u, v) for u, v, d in G.edges(data=True) if d['weight'] < 0]

# Draw positive correlation edges in green, negative correlation edges in red
nx.draw_networkx_edges(G, pos, edgelist=pos_corr_edges, edge_color='g', width=[2 * G[u][v]['weight'] for u, v in pos_corr_edges])
nx.draw_networkx_edges(G, pos, edgelist=neg_corr_edges, edge_color='r', width=[2 * abs(G[u][v]['weight']) for u, v in neg_corr_edges])

# Draw nodes with different colors based on the degree (number of connections)
node_colors = [G.degree(node) for node in G.nodes()]
nx.draw_networkx_nodes(G, pos, node_size=500, node_color=node_colors, cmap=plt.cm.PuRd, alpha=0.9)

# Draw labels for nodes
nx.draw_networkx_labels(G, pos, font_size=12, font_family='sans-serif')

# Draw edge labels with correlation values
edge_labels = {(u, v): f'{d["weight"]:.2f}' for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10, label_pos=0.3)

# Set axis off
plt.axis('off')

# Show the plot
plt.show()
