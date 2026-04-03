import networkx as nx
from pyvis.network import Network

class GraphBuilder:
    def __init__(self):
        self.nodes = set()
        self.edges = set()
        self.xpath_map = {} # New: GraphBuilder now accepts the map

    def build_interactive_graph(self, output_file):
        G = nx.DiGraph()

        for node in self.nodes:
            # Strip the trailing slash first, ensures you get the page name
            short_label = node.rstrip('/').split('/')[-1] or node
            # Use 'Link Position' metadata since XPath was missing in this export
            pos_info = self.xpath_map.get(node, "N/A")
            
            G.add_node(
                node, 
                label=short_label, 
                title=f"Location: {pos_info}\nFull URL: {node}",
                color="#97c2fc"
            )
        
        # Add edges
        G.add_edges_from(self.edges)

        # Optimization: Initialise PyVis
        net = Network(
            height="750px", 
            width="100%", 
            bgcolor="#222222", 
            font_color="white", 
            directed=True
        )
        net.from_nx(G)
        
        # Performance
        net.barnes_hut(
            gravity=-2000, 
            central_gravity=0.3, 
            spring_length=150, 
            spring_strength=0.05, 
            damping=0.09, 
            overlap=0
        )
        # This prevents the "infinite loading" by stopping the 
        # physics after a few seconds
        net.set_options(
        """
        {
          "edges": {
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 1.1 }
            },
            "color": { "inherit": "from" },
            "smooth": { "type": "continuous" }
          },
          "physics": {
            "stabilization": {
              "enabled": true,
              "iterations": 100,
              "updateInterval": 25
            }
          }
        }
        """)

        # Save Output
        if not output_file.endswith(".html"):
            output_file = output_file.rsplit('.', 1)[0] + ".html"
        
        # Save file
        print(f"Generating interactive graph: {output_file}..")
        net.show(output_file, notebook=False)