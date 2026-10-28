from pathlib import Path

import pytest  #noqa
from pyvis.network import Network

from webatlas.graph_builder.html_injector import inject_custom_html


def test_inject_custom_html_success(tmp_path, monkeypatch):
    """
    Verify inject_custom_html normalizes extensions, 
    writes output, and injects custom JS/HTML.
    """
    
    # Mock Network.show to simulate PyVis file generation without opening a browser tab
    def mock_show(self, path, notebook=False):
        Path(path).write_text("<html><head></head><body>Original Content</body></html>", encoding="utf-8")

    monkeypatch.setattr(Network, "show", mock_show)

    # Pass a filename without .html to test extension correction
    output_target = tmp_path / "visualization_output"
    net = Network()
    
    node_colors_dict = {"https://example.com/": "#2ecc71"}
    silos_dict = {"Homepage": ["https://example.com/"]}

    inject_custom_html(net, str(output_target), node_colors_dict, silos_dict)

    # Verify extension was normalized to .html
    expected_file = tmp_path / "visualization_output.html"
    assert expected_file.exists()

    # Read back the injected HTML content
    html_content = expected_file.read_text(encoding="utf-8")

    # Verify custom scripts and toolbars were successfully injected
    assert "var nodeColors = {\"https://example.com/\": \"#2ecc71\"}" in html_content
    assert "var silosMap = {\"Homepage\": [\"https://example.com/\"]}" in html_content
    assert 'id="silo-toolbar"' in html_content
    assert "physics" in html_content
    assert "Original Content" in html_content