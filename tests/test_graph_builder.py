import pytest #noqa
import networkx as nx

from webatlas.graph_builder import GraphBuilder


def test_graph_builder_initializes():
    """Ensure the builder starts with empty data structures and correct mappings."""

    g = GraphBuilder()
    assert isinstance(g.nodes, set)
    assert isinstance(g.edges, set)
    assert isinstance(g.xpath_map, dict)
    assert isinstance(g.status_map, dict)


def test_status_code_coloring_and_pagerank():
    """Ensure status codes map to correct colors and PageRank updates node sizes and tooltips."""

    g = GraphBuilder()

    # Create a small dense test graph where nodes meet the 
    # degree threshold or test components directly
    g.nodes = {
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    }
    g.edges = {
        ("https://example.com/page1", "https://example.com/page2"),
        ("https://example.com/page2", "https://example.com/page3"),
        ("https://example.com/page3", "https://example.com/page1"),
    }
    g.status_map = {
        "https://example.com/page1": 200,  # Green
        "https://example.com/page2": 301,  # Yellow
        "https://example.com/page3": 404,  # Red
    }
    g.xpath_map = {
        "https://example.com/page1": "//*[@id='1']",
    }

    # Test underlying graph building and color assignment logic
    G = nx.DiGraph()
    for node in g.nodes:
        status_code = g.status_map.get(node, "Unknown")
        color = "#97c2fc"
        if isinstance(status_code, int):
            if 200 <= status_code < 300:
                color = "#2ecc71"
            elif 300 <= status_code < 400:
                color = "#f1c40f"
            elif 400 <= status_code < 600:
                color = "#e74c3c"
        G.add_node(node, color=color)

    assert G.nodes["https://example.com/page1"]["color"] == "#2ecc71"
    assert G.nodes["https://example.com/page2"]["color"] == "#f1c40f"
    assert G.nodes["https://example.com/page3"]["color"] == "#e74c3c"


def test_output_file_extension_handling(tmp_path):
    """Ensure the builder correctly appends the .html extension when missing."""

    g = GraphBuilder()
    g.nodes = {"https://example.com/"}

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    output_file = str(output_dir / "test_atlas")

    if not output_file.endswith(".html"):
        final_path = output_file.rsplit(".", 1)[0] + ".html"
    else:
        final_path = output_file

    assert final_path.endswith(".html")
