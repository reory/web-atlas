import json
import logging
from typing import Any
from urllib.parse import urlparse

import networkx as nx
from pyvis.network import Network

logger = logging.getLogger(__name__)

DEFAULT_MIN_DEGREE = 50
DEFAULT_MAX_EDGES = 2000
DEFAULT_NODE_SIZE = 20
NODE_SIZE_RANGE = 40

 # Status Code Colour Coding Rules
STATUS_COLORS = {
    "default": "#97c2fc",
    "success": "#2ecc71",
    "redirect": "#f1c40f",
    "error": "#e74c3c",
}

def get_status_color(status_code):
    if not isinstance(status_code, int):
        return STATUS_COLORS["default"]
    if 200 <= status_code < 300:
        return STATUS_COLORS["success"]
    if 300 <= status_code < 400:
        return STATUS_COLORS["redirect"]
    if 400 <= status_code < 600:
        return STATUS_COLORS["error"]
        
    return STATUS_COLORS["default"]

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
        Generate an interactive graph from the current data 
        with status-code color, folder silo grouping, PageRank scaling,
        and inject nodeColors and category filters for utils.js.
        """

        logger.info("Initializing GraphBuilder and mapping nodes/edges....")

        G = nx.DiGraph()
        node_colors_dict = {}
        silos_dict = {}

        for node in self.nodes:
            # Skip URLs containing query parameters (like feeds, tracking links, parameters)
            if "?" in node:
                continue
            # Strip the trailing slash first, ensures you get the page name
            short_label = node.rstrip("/").split("/")[-1] or node
            # Use 'Link Position' metadata since XPath was missing in this export
            pos_info = self.xpath_map.get(node, "N/A")
            status_code = self.status_map.get(node, "Unknown")

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
        node_lookup = {n.rstrip("/"): n for n in self.nodes}

        # Check direct match or clean match using lookup dictionary
        added_edges = 0
        for u, v in self.edges:
            u_clean = u.rstrip("/")
            v_clean = v.rstrip("/")

            if u in self.nodes and v in self.nodes:
                G.add_edge(u, v, color="#ffff00", width=2)
                added_edges += 1

            elif u_clean in node_lookup and v_clean in node_lookup:
                orig_u = node_lookup[u_clean]
                orig_v = node_lookup[v_clean]
                G.add_edge(orig_u, orig_v, color="#ffff00", width=2)
                added_edges += 1

        logger.info(f"Total nodes built: {len(self.nodes)} | Total raw edges: {len(self.edges)}")
        logger.info(f"Successfully added edges to graph: {added_edges}")

        #-------------------------------------------------------------------
        # IMPORTANT: Insert node filtering
        # Adjust threshold of nodes you want to show.
        # 200 is the sweet spot any lower and you will see more nodes and their
        # associations which will overwhelm the website display.
        min_degree = DEFAULT_MIN_DEGREE
        nodes_to_remove = []
        for node, degree in G.degree():
            if degree < min_degree:
                # Check if this node is the homepage (root path is empty or "/")
                parsed_path = urlparse(node).path.strip("/")
                if parsed_path == "":
                    continue
                nodes_to_remove.append(node)

        G.remove_nodes_from(nodes_to_remove)
        #--------------------------------------------------------------------

        # Remove self-loops
        G.remove_edges_from(list(nx.selfloop_edges(G)))
        
        # Edge capping for heavy graphs
        max_edges = DEFAULT_MAX_EDGES
        if G.number_of_edges() > max_edges:
            # Create a new graph or remove excess edges
            excess_edges = list(G.edges())[max_edges:]
            G.remove_edges_from(excess_edges)

        # Prune the color dict to match only the nodes that survived the filtering
        node_colors_dict = {node: color for node, color in node_colors_dict.items() if node in G}

        # Build surviving silos dictionary for UI filtering
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
                node_size = int(DEFAULT_NODE_SIZE + (norm_score * 
                NODE_SIZE_RANGE))
                G.nodes[node]["size"] = node_size

                # Append PageRank score to the hover tooltip title
                current_title = G.nodes[node].get("title", "")
                G.nodes[node]["title"] = f"{current_title}\nPageRank: {score:.4f}"

        logger.info("Calculated PageRank scores and applied dynamically node scaling.")

        logger.info(f"Filtered out {len(nodes_to_remove)} low-degree nodes (degree < {min_degree}).")
        logger.info(f"Remaining nodes for visualisation: {G.number_of_nodes()}")

        # Optimization: Initialise PyVis
        net = Network(
            height="750px",
            width="100%",
            bgcolor="#",
            font_color="#333333",
            directed=True,
        )
        net.from_nx(G)

        # Ensure PyVis edge objects respect properties
        for edge in net.edges:
            edge["color"] = "#333333"
            edge["width"] = 2
            edge["opacity"] = 0.8

        # Performance & Visible Edge Options
        net.barnes_hut(
            gravity=-5000,
            central_gravity=0.3,
            spring_length=200,
            spring_strength=0.04,
            damping=0.09,
            overlap=0,
        )
        # Performance & Edge Styling Options
        net.set_options(
            """
            {
              "edges": {
                "arrows": {
                  "to": { "enabled": true, "scaleFactor": 0.5 }
                },
                "color": {
                  "color": "#ffff00",
                  "highlight": "#ffffff",
                  "opacity": 0.8
                },
                "width": 2,
                "smooth": { "type": "continuous" }
              },
              "physics": {
                "barnesHut": {
                  "gravitationalConstant": -15000,
                  "centralGravity": 0.1,
                  "springLength": 300,
                  "springConstant": 0.01,
                  "damping": 0.09
                },
                "stabilization": {
                  "enabled": true,
                  "iterations": 1000,
                  "updateInterval": 50,
                  "fit": true
                },
                "solver": "barnesHut"
              }
            }
            """
        )

        # Save Output
        if not output_file.endswith(".html"):
            output_file = output_file.rsplit(".", 1)[0] + ".html"

        # Save file
        try:
            logger.info(f"Generating interactive graph file: {output_file}....")
            net.show(output_file, notebook=False)

            # Read back the HTML to inject custom behaviors 
            # (like freezing physics and color dict)
            with open(output_file, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Script to freeze physics completely once stabilization completes
            physics_freeze_script = """
            <script type="text/javascript">
                window.addEventListener("load", function() {
                    if (typeof network !== "undefined") {
                        network.once("stabilizationIterationsDone", function() {
                            network.setOptions({ physics: false });
                        });
                    }
                });
            </script>
            """

            # Safely serialize Python dicts to JS using json.dumps
            color_injection = f"""
            <script>
            var nodeColors = {json.dumps(node_colors_dict)};
            var silosMap = {json.dumps(silos_dict)};
            </script>
            """

            # Interactive Silo Toolbar HTML & JavaScript Control
            silo_toolbar_html = """
            <div id="silo-toolbar" style="position: absolute; top: 15px; left: 15px; z-index: 1000; background: rgba(255, 255, 255, 0.95); padding: 10px 14px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); font-family: sans-serif; width: 320px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 12px; color: #333;">Folder Silos:</strong>
                    <div style="font-size: 10px; display: flex; gap: 6px;">
                        <span style="color: #2ecc71; font-weight: bold;">■ 200</span>
                        <span style="color: #f1c40f; font-weight: bold;">■ Redirect</span>
                        <span style="color: #e74c3c; font-weight: bold;">■ Error</span>
                    </div>
                </div>
                <div id="silo-buttons" style="display: flex; flex-wrap: wrap; gap: 4px; max-height: 130px; overflow-y: auto; padding-right: 4px;">
                    <button onclick="filterSilo('ALL', this)" style="padding: 3px 8px; font-size: 10px; cursor: pointer; background: #333; color: #fff; border: none; border-radius: 4px;">All</button>
                </div>
            </div>
            <script type="text/javascript">
                window.addEventListener("load", function() {
                    if (typeof silosMap !== "undefined" && document.getElementById("silo-buttons")) {
                        const container = document.getElementById("silo-buttons");
                        Object.keys(silosMap).forEach(silo => {
                            const btn = document.createElement("button");
                            btn.innerText = silo;
                            btn.style.padding = "3px 8px";
                            btn.style.fontSize = "10px";
                            btn.style.cursor = "pointer";
                            btn.style.background = "#e0e0e0";
                            btn.style.color = "#333";
                            btn.style.border = "none";
                            btn.style.borderRadius = "4px";
                            btn.onclick = () => filterSilo(silo, btn);
                            container.appendChild(btn);
                        });
                    }
                });

                function filterSilo(targetSilo, clickedBtn) {
                    if (typeof nodes === "undefined") return;
                    
                    // Update active button styles across the toolbar
                    const allButtons = document.querySelectorAll("#silo-buttons button");
                    allButtons.forEach(b => {
                        b.style.background = "#e0e0e0";
                        b.style.color = "#333";
                    });
                    if (clickedBtn) {
                        clickedBtn.style.background = "#333";
                        clickedBtn.style.color = "#fff";
                    }

                    const allNodes = nodes.get();
                    const targetList = silosMap[targetSilo] || [];

                    const updatedNodes = allNodes.map(node => {
                        if (targetSilo === 'ALL') {
                            node.hidden = false;
                        } else {
                            // Check exact ID match or fuzzy match
                            const isMatch = targetList.includes(node.id) || targetList.some(item => node.id.includes(item) || item.includes(node.id));
                            node.hidden = !isMatch;
                        }
                        return node;
                    });
                    nodes.update(updatedNodes);
                }
            </script>
            """

            # Correctly replace single </body> without duplicating it
            injection_payload = physics_freeze_script + color_injection + silo_toolbar_html + "\n</body>"
            html_content = html_content.replace("</body>", injection_payload)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(f"Successfully generated and finalised: {output_file}")

        except Exception:
            logger.exception(f"Failed to generate or write interactive graph output to {output_file}:")
            raise
