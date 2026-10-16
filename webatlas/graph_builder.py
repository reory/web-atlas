import logging

import networkx as nx
from pyvis.network import Network

logger = logging.getLogger(__name__)


class GraphBuilder:
    def __init__(self, sf_importer=None):
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

    def build_interactive_graph(self, output_file):
        """
        Generate an interactive graph from the current data 
        with status-code color coding and inject nodeColors for utils.js.
        """

        logger.info("Initializing GraphBuilder and mapping nodes/edges....")

        G = nx.DiGraph()
        node_colors_dict = {}

        for node in self.nodes:
            # Strip the trailing slash first, ensures you get the page name
            short_label = node.rstrip("/").split("/")[-1] or node
            # Use 'Link Position' metadata since XPath was missing in this export
            pos_info = self.xpath_map.get(node, "N/A")
            status_code = self.status_map.get(node, "Unknown")

            # Status Code Colour Coding Rules
            color = "#97c2fc" #Default blue for unknown / external
            if isinstance(status_code, int):
                if 200 <= status_code < 300:
                    color = "#2ecc71" # Green: 200 Ok
                elif 300 <= status_code < 400:
                    color = "#f1c40f" # Yellow: 301/302 Redirects
                elif 400 <= status_code < 600:
                    color = "#e74c3c" # Red: 404/500 Errors
            node_colors_dict[node] = color

            G.add_node(
                node,
                label=short_label,
                title=f"Location: {pos_info}\nFull URL: {node}",
                color=color,
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
        # associations.
        min_degree = 200
        nodes_to_remove = [node for node, degree in G.degree() if degree < min_degree]
        G.remove_nodes_from(nodes_to_remove)
        #--------------------------------------------------------------------

        # Remove self-loops
        G.remove_edges_from(list(nx.selfloop_edges(G)))
        
        # Edge capping for heavy graphs
        max_edges = 2000
        if G.number_of_edges() > max_edges:
            # Create a new graph or remove excess edges
            excess_edges = list(G.edges())[max_edges:]
            G.remove_edges_from(excess_edges)

        # Prune the color dict to match only the nodes that survived the filtering
        node_colors_dict = {node: color for node, color in node_colors_dict.items() if node in G}

        # Calculate PageRank and scale nodes sizes dynamically
        pagerank_scores = nx.pagerank(G, alpha=0.85)

        if pagerank_scores:
            min_pr = min(pagerank_scores.values())
            max_pr = max(pagerank_scores.values())
            pr_range = (max_pr - min_pr) if (max_pr - min_pr) > 0 else 1.0

            for node in G.nodes():
                score = pagerank_scores.get(node, min_pr)
                # Normalise between 0 and 1, then scale to a pixel size range.
                norm_score = (score - min_pr) / pr_range
                node_size = int(20 + (norm_score * 40))
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

            color_injection = f"\n<script>\nvar nodeColors = {node_colors_dict};\n</script>\n"

            # Inject both into HTML body/end
            html_content = html_content.replace("</body>", physics_freeze_script + color_injection + "</body>")

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(f"Successfully generated and finalised: {output_file}")

        except Exception:
            logger.exception(f"Failed to generate or write interactive graph output to {output_file}:")
            raise
