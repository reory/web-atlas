import pytest #noqa

from webatlas.graph_builder.builder import GraphBuilder


class MockImporter:
    """Mock ScreamingFrogImporter for testing GraphBuilder."""

    def __init__(self):
        self.nodes = {"https://example.com/", "https://example.com/about"}
        self.edges = {("https://example.com/", "https://example.com/about")}
        self.xpath_map = {"https://example.com/about": "/html/body/a"}
        self.status_map = {"https://example.com/": 200, "https://example.com/about": 200}


class TestGraphBuilder:
    """Test suite for the GraphBuilder orchestrator class."""

    def test_init_empty(self):
        """
        Verify GraphBuilder initializes with empty 
        collections when no importer is provided.
        """

        builder = GraphBuilder()
        assert builder.nodes == set()
        assert builder.edges == set()
        assert builder.xpath_map == {}
        assert builder.status_map == {}

    def test_init_with_importer(self):
        """Verify GraphBuilder correctly assigns attributes from an importer object."""

        importer = MockImporter()
        builder = GraphBuilder(importer)
        assert builder.nodes == importer.nodes
        assert builder.edges == importer.edges
        assert builder.xpath_map == importer.xpath_map
        assert builder.status_map == importer.status_map

    def test_build_interactive_graph_orchestration(self, tmp_path, monkeypatch):
        """Verify build_interactive_graph successfully executes the pipeline and generates output."""

        from webatlas.graph_builder import builder as builder_module

        # Lower minimum degree threshold so test nodes survive filtering
        monkeypatch.setattr(builder_module, "DEFAULT_MIN_DEGREE", 1)

        importer = MockImporter()
        builder = GraphBuilder(importer)

        output_file = tmp_path / "test_graph.html"

        # Execute orchestrator method
        builder.build_interactive_graph(str(output_file))

        # Verify that the output HTML file was successfully created by PyVis/injector
        assert output_file.exists()
        assert output_file.stat().st_size > 0