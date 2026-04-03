import argparse
import logging
import sys
from webatlas.sf_import import ScreamingFrogImport
from webatlas.graph_builder import GraphBuilder

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        # Professional audit trail
        logging.FileHandler("webatlas_pipeline.log"), 
        # Real-time terminal feedback 
        logging.StreamHandler(sys.stdout)             
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="WebAtlas - Build an interactive link graph")
    parser.add_argument(
        "--xlsx", 
        nargs=2, 
        metavar=("INTERNAL", "OUTLINKS"), 
        required=True
    )
    parser.add_argument("output", help="Output HTML file (e.g., atlas.html)")
    return parser.parse_args()

def main():
    args = parse_args()
    internal_xlsx, outlinks_xlsx = args.xlsx
    output_file = args.output

    logger.info("Webatlas pipeline starting..")
    try:
        # Import Data
        logger.info(f"Importing data from {internal_xlsx} and {outlinks_xlsx}..")
        importer = ScreamingFrogImport().load(internal_xlsx, outlinks_xlsx)
        logger.info(f"Data imported successfully. Found {len(
            importer.nodes)} nodes and {len(
            importer.edges)} edges"
        )

        # Build Graph
        logger.info("Initialising GraphBuilder and mapping XPaths..")
        graph = GraphBuilder()
        graph.nodes = importer.nodes
        graph.edges = importer.edges
        # Step 2: Pass the XPath map to the builder
        graph.xpath_map = importer.xpath_map 

        # Generate Interactive HTML (Replacing write_dot)
        logger.info(f"Generating Interactive Mothball: {output_file}")
        logger.info("Note: Stabilisation physics may take 10 secs for large crawls.")
        graph.build_interactive_graph(output_file)

        logger.info(f"Pipeline completed!  Output saved to: {output_file}")
    
    except Exception as e:
        logger.error(f"Pipeline Failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()