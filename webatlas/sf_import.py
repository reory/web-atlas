import logging
from urllib.parse import urljoin, urlparse

from openpyxl import load_workbook

logger = logging.getLogger(__name__)


class ScreamingFrogImport:
    """
    Universal Screaming Frog importer optimized for PyVis visualization.
    Filters out non-hyperlinks to keep the graph fast and clean.
    """

    def __init__(self):
        self.nodes = set()
        self.edges = set()
        self.xpath_map = {}  # Maps URL -> XPath (or Link Position) for tooltips
        self.status_map = {} # Maps URL -> HTTP Status Code

    def load_internal(self, internal_xlsx):
        """
        Load internal data from the given Excel file and update
        the object's state with flexible header matching.
        """

        logger.info(f"Loading internal pages from workbook: {internal_xlsx}...")
        wb = load_workbook(internal_xlsx, data_only=True)
        ws = wb.active
        root_url = None

        raw_header = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        header = [str(h).strip() if h else "" for h in raw_header]

        # Find address column flexibly (case-insensitive)
        addr_idx = None
        for idx, h in enumerate(header):
            h_lower = h.lower()
            if "address" in h_lower or h_lower == "url":
                addr_idx = idx
                break

        # Identify status column flexibly
        status_idx = None
        for idx, h in enumerate(header):
            h_lower = h.lower()
            if "status" in h_lower:
                status_idx = idx
                break

        if addr_idx is not None:
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) <= addr_idx:
                    continue
                url = row[addr_idx]
                if isinstance(url, str) and url.startswith(("http://", "https://")):
                    if root_url is None:
                        root_url = url
                    self.nodes.add(url)

                    # Capture Status Code
                    if status_idx is not None and row[status_idx] is not None:
                        try:
                            self.status_map[url] = int(row[status_idx])
                        except (ValueError, TypeError):
                            self.status_map[url] = row[status_idx]

        # Fallback: Scan all cells in the sheet for a valid HTTP URL 
        # if header lookup missed it
        if not root_url:
            logger.warning(
                "Standard address header lookup missed root URL;"
                "performing deep scan"
            )
            for row in ws.iter_rows(min_row=2, values_only=True):
                for cell in row:
                    if isinstance(cell, str) and cell.startswith(("http://", "https://")):
                        root_url = cell
                        self.nodes.add(cell)
                        break
                if root_url:
                    break

        if not root_url:
            error_msg = f"Could not extract root URL from {internal_xlsx}."
            f"Detected headers were: {header}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.root_url = root_url
        logger.info(f"Successfully loaded internal data. Root URL identified: {root_url}")
        return root_url


    def load_outlinks(self, outlinks_xlsx):
        """
        Load outlink data from the given
        Excel file and update the object's state.
        """
        
        logger.info(f"Loading outlinks from workbook: {outlinks_xlsx}...")
        wb = load_workbook(outlinks_xlsx, data_only=True)
        ws = wb.active

        # Clean Headers
        raw_header = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        header = [str(h).strip() if h else "" for h in raw_header]

        # Identify Column Indices flexibly based on actual headers
        try:
            # Screaming Frog standard outlinks typically use 'Source' and 'Destination'
            origin_idx = header.index(
                "Source") if "Source" in header else header.index("Link Origin"
            )
            path_idx = header.index(
                "Destination") if "Destination" in header else (header.index(
                    "Link Path") if "Link Path" in header else header.index(
                        "Target")
            )
            type_idx = header.index("Type")

            # Find XPath column (usually 'Path' in SF)
            if "Path" in header:
                xpath_idx = header.index("Path")
            else:
                # Fallback to any header containing 'XPath' or use 'Link Position'
                xpath_idx = next(
                    (
                        i
                        for i, h in enumerate(header)
                        if "XPath" in h or "Position" in h
                    ),
                    None,
                )

        except ValueError as e:
            error_msg = "Outlink file missing required columns"
            "(Source/Origin, Destination/Path, Type)." 
            f"Detected headers: {header}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

        # Get root domain netloc for internal filtering
        root_netloc = urlparse(getattr(self, "root_url", "")).netloc

        # Process Rows
        added_count = 0
        skipped_external = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            # Skip empty rows
            if not row[origin_idx] or not row[path_idx]:
                continue

            # Only process actual links (ignores images, CSS, JS)
            if row[type_idx] != "Hyperlink":
                continue

            origin = str(row[origin_idx])
            link_path = str(row[path_idx])
            xpath_value = row[xpath_idx] if xpath_idx is not None else "N/A"

            # Normalize Destination URL
            if link_path.startswith(("http://", "https://")):
                dest = link_path
            else:
                dest = urljoin(origin, link_path)

            # Domain filter: Skip external links using root_netloc
            if root_netloc:
                dest_netloc = urlparse(dest).netloc
                if dest_netloc and dest_netloc != root_netloc:
                    continue

            # Store Data for internal links only
            self.nodes.add(origin)
            self.nodes.add(dest)
            self.edges.add((origin, dest))
            self.xpath_map[dest] = xpath_value
            added_count += 1

        logger.info(
            f"Successfully processed {added_count} internal outlinks"
            f"(skipped {skipped_external} external links)."
        )
        return self.edges

    def load(self, internal_xlsx, outlinks_xlsx):
        """
        Load internal and outlink data from the given
        Excel files and refresh the object's state.
        """

        self.load_internal(internal_xlsx)
        self.load_outlinks(outlinks_xlsx)
        return self
