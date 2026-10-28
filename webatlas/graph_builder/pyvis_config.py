"""Handles PyVis network instantiation and physics options."""

import networkx as nx
from pyvis.network import Network


def configure_pyvis_network(G: nx.DiGraph) -> Network:
    """Initialise PyVis network instance and apply physical simulation options."""

# Optimization: Initialise PyVis
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#",
        font_color="#333333",
        directed=True,
    )
    net.from_nx(G)

    # Ensure PyVis edge objects respect properties
    for edge in net.edges:
        edge["color"] = "#333333"
        edge["width"] = 2
        edge["opacity"] = 0.8

    # Performance & Visible Edge Options
    net.barnes_hut(
        gravity=-5000,
        central_gravity=0.3,
        spring_length=200,
        spring_strength=0.04,
        damping=0.09,
        overlap=0,
    )
    # Performance & Edge Styling Options
    net.set_options(
        """
        {
            "edges": {
              "arrows": {
                "to": { "enabled": true, "scaleFactor": 0.5 }
              },
              "color": {
                "color": "#ffff00",
                "highlight": "#ffffff",
                "opacity": 0.8
              },
              "width": 2,
              "smooth": { "type": "continuous" }
            },
            "physics": {
              "barnesHut": {
                "gravitationalConstant": -15000,
                "centralGravity": 0.1,
                "springLength": 300,
                "springConstant": 0.01,
                "damping": 0.09
              },
              "stabilization": {
                "enabled": true,
                "iterations": 1000,
                "updateInterval": 50,
                "fit": true
              },
              "solver": "barnesHut"
            }
          }
          """
    )
    return net