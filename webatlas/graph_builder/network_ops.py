"""
Handles NetworkX graph construction, 
filtering, edge capping, and PageRank calculations.
"""

import logging
from urllib.parse import urlparse

import networkx as nx

from .constants import (
    DEFAULT_MAX_EDGES,
    DEFAULT_MIN_DEGREE,
    DEFAULT_NODE_SIZE,
    NODE_SIZE_RANGE,
    get_status_color,
)

logger = logging.getLogger(__name__)


def build_networkx_graph(
    nodes: set, edges: set, xpath_map: dict, status_map: dict
) -> tuple[nx.DiGraph, dict[str, str]]:
    """Construct the initial directed NetworkX graph and color dictionary."""

    logger.info("Initializing GraphBuilder and mapping nodes/edges....")

    G = nx.DiGraph()
    node_colors_dict = {}

    for node in nodes:
        # Skip URLs containing query parameters (like feeds, tracking links, parameters)
        if "?" in node:
                continue
        # Strip the trailing slash first, ensures you get the page name
        short_label = node.rstrip("/").split("/")[-1] or node
        # Use 'Link Position' metadata since XPath was missing in this export
        pos_info = xpath_map.get(node, "N/A")
        status_code = status_map.get(node, "Unknown")

        # Extract Folder Silo via Python string parsing
        parsed_path = urlparse(node).path.strip("/")
        segments = parsed_path.split("/")
        silo = f"/{segments[0]}/" if segments and segments[0] else "Homepage"

        color = get_status_color(status_code)

        node_colors_dict[node] = color

        G.add_node(
            node,
            label=short_label,
            title=f"Status: {status_code}\nSilo: {silo}\nLocation: {pos_info}\nFull URL: {node}",
            color=color,
            silo=silo,
        )

    # Create a mapping from clean URL to the original exact node name
    node_lookup = {n.rstrip("/"): n for n in nodes}

    # Check direct match or clean match using lookup dictionary
    added_edges = 0
    for u, v in edges:
        u_clean = u.rstrip("/")
        v_clean = v.rstrip("/")

        if u in nodes and v in nodes:
            G.add_edge(u, v, color="#ffff00", width=2)
            added_edges += 1

        elif u_clean in node_lookup and v_clean in node_lookup:
            orig_u = node_lookup[u_clean]
            orig_v = node_lookup[v_clean]
            G.add_edge(orig_u, orig_v, color="#ffff00", width=2)
            added_edges += 1

    logger.info(f"Total nodes built: {len(nodes)} | Total raw edges: {len(edges)}")
    logger.info(f"Successfully added edges to graph: {added_edges}")
    return G, node_colors_dict


def apply_filters_and_pagerank(
    G: nx.DiGraph, node_colors_dict: dict[str, str]
) -> tuple[nx.DiGraph, dict[str, str], dict[str, list[str]], list[str]]:
    """Filter low-degree nodes, remove self-loops, cap edges, and calculate PageRank."""

    # IMPORTANT: Insert node filtering
    # Adjust threshold of nodes you want to show.
    # 200 is the sweet spot any lower and you will see more nodes and their
    # associations which will overwhelm the website display.
    nodes_to_remove = []
    for node, degree in G.degree():
        if degree < DEFAULT_MIN_DEGREE:
            # Check if this node is the homepage (root path is empty or "/")
            parsed_path = urlparse(node).path.strip("/")
            if parsed_path == "":
                continue
            nodes_to_remove.append(node)

    G.remove_nodes_from(nodes_to_remove)
    # Remove self-loops
    G.remove_edges_from(list(nx.selfloop_edges(G)))
        
    # Edge capping for heavy graphs
    if G.number_of_edges() > DEFAULT_MAX_EDGES:
        # Create a new graph or remove excess edges
        excess_edges = list(G.edges())[DEFAULT_MAX_EDGES:]
        G.remove_edges_from(excess_edges)

    # Prune the color dict to match only the nodes that survived the filtering
    node_colors_dict = {node: color for node, color in node_colors_dict.items() if node in G}

    # Build surviving silos dictionary for UI filtering
    silos_dict: dict[str, list[str]] = {}
    for node in G.nodes():
        parsed_path = urlparse(node).path.strip("/")
        segments = parsed_path.split("/")
        node_silo = f"/{segments[0]}/" if segments and segments[0] else "Homepage"

        if node_silo not in silos_dict:
            silos_dict[node_silo] = []
        silos_dict[node_silo].append(node)

    # Calculate PageRank and scale nodes sizes dynamically
    if G.number_of_nodes() > 0:
        pagerank_scores = nx.pagerank(G, alpha=0.85)
    else:
        logger.warning(
            "Graph is empty after filtering, skipping PageRank calculation."
        )
        pagerank_scores = {}

    if pagerank_scores:
        min_pr = min(pagerank_scores.values())
        max_pr = max(pagerank_scores.values())
        pr_range = (max_pr - min_pr) if (max_pr - min_pr) > 0 else 1.0

        for node in G.nodes():
            score = pagerank_scores.get(node, min_pr)
            # Normalise between 0 and 1, then scale to a pixel size range.
            norm_score = (score - min_pr) / pr_range
            node_size = int(DEFAULT_NODE_SIZE + (norm_score * NODE_SIZE_RANGE))
            G.nodes[node]["size"] = node_size

            # Attach raw metrics for client-side slider filtering
            G.nodes[node]["degree"] = G.degree(node)
            G.nodes[node]["pagerank"] = score

            # Append PageRank score to the hover tooltip title
            current_title = G.nodes[node].get("title", "")
            if current_title:
                G.nodes[node]["title"] = f"{current_title}\nPageRank: {score:.4f}"
            else:
                G.nodes[node]["title"] = f"PageRank: {score:.4f}"

    logger.info("Calculated PageRank scores and applied dynamically node scaling.")
    return G, node_colors_dict, silos_dict, nodes_to_remove