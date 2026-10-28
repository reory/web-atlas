from pathlib import Path

import openpyxl
import pytest

from webatlas.sf_imports import ScreamingFrogImport


@pytest.fixture
def create_excel_file(tmp_path: Path):
    """Helper fixture to construct temporary Excel workbooks for testing."""

    def _create_file(filename: str, rows: list[list]):
        file_path = tmp_path / filename
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        wb.save(file_path)
        return str(file_path)

    return _create_file


class TestScreamingFrogImportEdgeCases:
    """Edge case test suite for ScreamingFrogImport."""

    def test_external_domain_filtering(self, create_excel_file):
        """Verify that external domains are filtered out during outlink processing."""

        internal_rows = [
            ["Address", "Status Code"],
            ["https://example.com/", 200],
        ]
        outlinks_rows = [
            ["Source", "Destination", "Type", "Path"],
            ["https://example.com/", "https://external-domain.com/page", "Hyperlink", "/html/body/a"],
        ]

        internal_path = create_excel_file("internal_ext.xlsx", internal_rows)
        outlinks_path = create_excel_file("outlinks_ext.xlsx", outlinks_rows)

        importer = ScreamingFrogImport()
        importer.root_url = importer.load_internal(internal_path)
        importer.load_outlinks(outlinks_path)

        # External domains must be filtered out of edges and xpath_map
        assert ("https://example.com/", "https://external-domain.com/page") not in importer.edges
        assert "https://external-domain.com/page" not in importer.xpath_map

    def test_url_with_port_number(self, create_excel_file):
        """Verify handling of URLs containing explicit port numbers."""

        internal_rows = [
            ["Address", "Status Code"],
            ["https://example.com:8080/", 200],
        ]
        outlinks_rows = [
            ["Source", "Destination", "Type", "Path"],
            ["https://example.com:8080/", "https://example.com:8080/about", "Hyperlink", "/html/body/div/a"],
        ]

        internal_path = create_excel_file("internal_port.xlsx", internal_rows)
        outlinks_path = create_excel_file("outlinks_port.xlsx", outlinks_rows)

        importer = ScreamingFrogImport()
        importer.root_url = importer.load_internal(internal_path)
        importer.load_outlinks(outlinks_path)

        # Netloc includes port (:8080), matching successfully when root also has port
        assert ("https://example.com:8080/", "https://example.com:8080/about") in importer.edges
        assert importer.xpath_map["https://example.com:8080/about"] == "/html/body/div/a"

    def test_special_characters_and_attributes_in_xpath(self, create_excel_file):
        """Verify that complex XPaths with attributes and quotes are stored correctly."""

        internal_rows = [
            ["Address", "Status Code"],
            ["https://example.com/", 200],
        ]
        outlinks_rows = [
            ["Source", "Destination", "Type", "Path"],
            [
                "https://example.com/",
                "https://example.com/special",
                "Hyperlink",
                "/html/body/div[@id='main-content']/nav[@class='primary']/ul/li[1]/a",
            ],
        ]

        internal_path = create_excel_file("internal_xpath.xlsx", internal_rows)
        outlinks_path = create_excel_file("outlinks_xpath.xlsx", outlinks_rows)

        importer = ScreamingFrogImport()
        importer.root_url = importer.load_internal(internal_path)
        importer.load_outlinks(outlinks_path)

        expected_xpath = "/html/body/div[@id='main-content']/nav[@class='primary']/ul/li[1]/a"
        assert importer.xpath_map["https://example.com/special"] == expected_xpath