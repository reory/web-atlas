from openpyxl import load_workbook
from urllib.parse import urljoin

class ScreamingFrogImport:
    """
    Universal Screaming Frog importer optimized for PyVis visualization.
    Filters out non-hyperlinks to keep the graph fast and clean.
    """

    def __init__(self):
        self.nodes = set()
        self.edges = set()
        self.xpath_map = {} # Maps URL -> XPath (or Link Position) for tooltips

    def load_internal(self, internal_xlsx):
        wb = load_workbook(internal_xlsx, data_only=True)
        ws = wb.active
        root_url = None
        
        raw_header = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        header = [str(h).strip() if h else "" for h in raw_header]

        if "Address" in header:
            addr_idx = header.index("Address")
            for row in ws.iter_rows(min_row=2, values_only=True):
                url = row[addr_idx]
                if isinstance(url, str) and url.startswith(("http://", "https://")):
                    root_url = url
                    break

        if not root_url:
            for name, value, *rest in ws.iter_rows(min_row=2, values_only=True):
                if name == "Address":
                    root_url = value
                    break
        
        if not root_url:
            raise ValueError("Could not extract root URL from internal.xlsx")

        self.nodes.add(root_url)
        self.root_url = root_url
        return root_url

    def load_outlinks(self, outlinks_xlsx):
        wb = load_workbook(outlinks_xlsx, data_only=True)
        ws = wb.active

        # 1. Clean Headers
        raw_header = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        header = [str(h).strip() if h else "" for h in raw_header]
        print(f"Detected Headers: {header}")

        # Identify Column Indices
        try:
            origin_idx = header.index("Link Origin")
            path_idx = header.index("Link Path")
            type_idx = header.index("Type")
            
            # Find XPath column (usually 'Path' in SF)
            if "Path" in header:
                xpath_idx = header.index("Path")
            else:
                # Fallback to any header containing 'XPath' or use 'Link Position'
                xpath_idx = next((
                    i for i, h in enumerate(header) 
                    if "XPath" in h or "Position" in h), None
                )

        except ValueError:
            raise ValueError(
                "Outlinks file missing required columns "
                "(Link Origin, Link Path, Type). Found: {header}"
            )

        # Process Rows
        for row in ws.iter_rows(min_row=2, values_only=True):
            # Skip empty rows
            if not row[origin_idx] or not row[path_idx]:
                continue

            # SPEED FIX: Only process actual links (ignores images, CSS, JS)
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

            # Store Data
            self.nodes.add(origin)
            self.nodes.add(dest)
            self.edges.add((origin, dest))
            
            # Save metadata for the tooltip
            self.xpath_map[dest] = xpath_value

        return self.edges

    def load(self, internal_xlsx, outlinks_xlsx):
        self.load_internal(internal_xlsx)
        self.load_outlinks(outlinks_xlsx)
        return self