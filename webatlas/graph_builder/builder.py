"""The main orchestrator class."""

import logging
from typing import Any

from .constants import DEFAULT_MIN_DEGREE
from .html_injector import inject_custom_html
from .network_ops import apply_filters_and_pagerank, build_networkx_graph
from .pyvis_config import configure_pyvis_network

logger = logging.getLogger(__name__)


class GraphBuilder:
    def __init__(self, sf_importer: Any | None = None) -> None:
        if sf_importer:
            self.nodes = sf_importer.nodes
            self.edges = sf_importer.edges
            self.xpath_map = sf_importer.xpath_map
            self.status_map = sf_importer.status_map
        else:
            self.nodes = set()
            self.edges = set()
            self.xpath_map = {}
            self.status_map = {}

    def build_interactive_graph(self, output_file: str) -> None:
        """
        Generate an interactive graph from current data with status-code coloring,
        folder silo grouping, PageRank scaling, and custom HTML/JS injection.
        """

        logger.info("Initializing GraphBuilder and mapping nodes/edges....")

        # Build base NetworkX graph
        G, node_colors_dict = build_networkx_graph(
            self.nodes, self.edges, self.xpath_map, self.status_map
        )

        # Apply degree filtering, edge capping, and PageRank scaling
        G, node_colors_dict, silos_dict, nodes_to_remove = apply_filters_and_pagerank(
            G, node_colors_dict
        )

        logger.info(f"Filtered out {len(nodes_to_remove)} low-degree nodes (degree < {DEFAULT_MIN_DEGREE}).")
        logger.info(f"Remaining nodes for visualisation: {G.number_of_nodes()}")

        # Initialize PyVis Network and apply layout options
        net = configure_pyvis_network(G)

        # Save output and inject custom toolbar / scripts
        inject_custom_html(net, output_file, node_colors_dict, silos_dict)