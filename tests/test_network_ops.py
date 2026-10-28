import networkx as nx
import pytest  #noqa

from webatlas.graph_builder import network_ops
from webatlas.graph_builder.network_ops import (
    apply_filters_and_pagerank,
    build_networkx_graph,
)


class TestNetworkOps:
    """Test suite for NetworkX graph construction and operations."""

    def test_build_networkx_graph_basic(self):
        """Verify graph construction, node attributes, silos, and color mapping."""

        nodes = {
            "https://example.com/",
            "https://example.com/blog",
            "https://example.com/blog/post-1",
            "https://example.com/feed?q=1",  # Should be filtered out due to '?'
        }
        edges = {
            ("https://example.com/", "https://example.com/blog"),
            ("https://example.com/blog", "https://example.com/blog/post-1"),
        }
        xpath_map = {
            "https://example.com/blog": "/html/body/nav/a",
        }
        status_map = {
            "https://example.com/": 200,
            "https://example.com/blog": 200,
            "https://example.com/blog/post-1": 404,
        }

        G, _node_colors = build_networkx_graph(nodes, edges, xpath_map, status_map)

        # Verify query parameter URLs are skipped
        assert "https://example.com/feed?q=1" not in G

        # Verify nodes and attributes
        assert "https://example.com/" in G
        assert G.nodes["https://example.com/"]["silo"] == "Homepage"
        assert G.nodes["https://example.com/blog"]["silo"] == "/blog/"
        assert G.nodes["https://example.com/blog"]["label"] == "blog"

        # Verify edges added
        assert G.has_edge("https://example.com/", "https://example.com/blog")
        assert G.has_edge("https://example.com/blog", "https://example.com/blog/post-1")

    def test_clean_url_edge_fallback(self):
        """Verify edge addition handles trailing slash mismatches via node lookup."""

        nodes = {"https://example.com/page-a/", "https://example.com/page-b"}
        edges = {("https://example.com/page-a", "https://example.com/page-b/")}
        xpath_map = {}
        status_map = {}

        G, _ = build_networkx_graph(nodes, edges, xpath_map, status_map)

        assert G.has_edge("https://example.com/page-a/", "https://example.com/page-b")

    def test_apply_filters_and_pagerank_preserves_homepage(self, monkeypatch):
        """Verify low-degree filtering removes isolated nodes but preserves the homepage."""

        # Lower the min degree threshold for testing so small test graphs survive
        monkeypatch.setattr(network_ops, "DEFAULT_MIN_DEGREE", 2)

        G = nx.DiGraph()
        # Homepage with low degree (degree 0) - should be preserved anyway
        G.add_node("https://example.com/", silo="Homepage")
        # Other low-degree node that should be filtered out
        G.add_node("https://example.com/orphan", silo="/orphan/")
        
        # Hub node with degree >= 2
        G.add_node("https://example.com/hub", silo="/hub/")
        G.add_node("https://example.com/child1", silo="/hub/")
        G.add_node("https://example.com/child2", silo="/hub/")
        
        G.add_edge("https://example.com/hub", "https://example.com/child1")
        G.add_edge("https://example.com/child2", "https://example.com/hub")
        G.add_edge("https://example.com/hub", "https://example.com/child2")

        node_colors = {
            "https://example.com/": "#00ff00",
            "https://example.com/orphan": "#ff0000",
            "https://example.com/hub": "#00ff00",
            "https://example.com/child1": "#00ff00",
            "https://example.com/child2": "#00ff00",
        }

        G_filtered, _colors_filtered, _silos, removed = apply_filters_and_pagerank(G, node_colors)

        # Homepage must be preserved despite low degree
        assert "https://example.com/" in G_filtered
        # Orphan node with low degree should be removed
        assert "https://example.com/orphan" in removed
        assert "https://example.com/orphan" not in G_filtered

        # Hub survives and has PageRank and size
        assert "https://example.com/hub" in G_filtered
        assert "PageRank:" in G_filtered.nodes["https://example.com/hub"]["title"]
        assert "size" in G_filtered.nodes["https://example.com/hub"]

    def test_remove_self_loops(self, monkeypatch):
        """Verify self-loops are stripped from the graph."""

        monkeypatch.setattr(network_ops, "DEFAULT_MIN_DEGREE", 1)

        G = nx.DiGraph()
        G.add_edge("https://example.com/", "https://example.com/")
        G.add_edge("https://example.com/", "https://example.com/about")
        G.add_edge("https://example.com/about", "https://example.com/")
        G.add_node("https://example.com/about", silo="/about/")

        node_colors = {"https://example.com/": "#00ff00", "https://example.com/about": "#00ff00"}

        G_filtered, _, _, _ = apply_filters_and_pagerank(G, node_colors)

        assert not list(nx.selfloop_edges(G_filtered))
        assert G_filtered.has_edge("https://example.com/", "https://example.com/about")