#!/usr/bin/env python
# coding: utf-8

# In[3]:


corr_matrix = df.corr()

import networkx as nx
import matplotlib.pyplot as plt

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
            G.add_edge(symbol1, symbol2, weight=abs(correlation))

# Draw the graph
plt.figure(figsize=(10, 10))
pos = nx.spring_layout(G)  # positions for all nodes
nx.draw_networkx_nodes(G, pos, node_size=500)
nx.draw_networkx_edges(G, pos, width=[G[u][v]['weight'] for u, v in G.edges()])
nx.draw_networkx_labels(G, pos, font_size=12, font_family='sans-serif')
plt.show()



# In[ ]:




