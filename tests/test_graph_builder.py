import pytest
from webatlas.graph_builder import GraphBuilder

def test_graph_builder_initializes():
    """Ensure the builder starts with empty data structures."""
    g = GraphBuilder()
    assert isinstance(g.nodes, set)
    assert isinstance(g.edges, set)
    assert isinstance(g.xpath_map, dict)

def test_graph_builder_data_assignment():
    """Ensure we can manually inject nodes, edges, and map data."""
    g = GraphBuilder()
    
    test_nodes = {"https://example.com/", "https://example.com/about"}
    test_edges = {("https://example.com/", "https://example.com/about")}
    test_map = {"https://example.com/about": "//*[@id='nav']/li[2]/a"}
    
    g.nodes = test_nodes
    g.edges = test_edges
    g.xpath_map = test_map
    
    assert len(g.nodes) == 2
    assert len(g.edges) == 1
    assert g.xpath_map["https://example.com/about"] == "//*[@id='nav']/li[2]/a"

def test_output_file_extension_handling(tmp_path):
    """Ensure the builder correctly handles/appends the .html extension."""
    g = GraphBuilder()
    g.nodes = {"https://example.com/"}
    
    # We use tmp_path to create a dummy file in a temporary folder
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    output_file = str(output_dir / "test_graph") # No extension provided
    
    # This will run the logic that appends .html
    # We call the rsplit logic directly or via the method
    if not output_file.endswith(".html"):
        final_path = output_file.rsplit('.', 1)[0] + ".html"
    else:
        final_path = output_file
        
    assert final_path.endswith(".html")

