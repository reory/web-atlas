import argparse
import logging
import sys
import warnings

# Suppress the missing default style warning from openpyxl
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.*")

from webatlas.graph_builder import GraphBuilder
from webatlas.sf_import import ScreamingFrogImport

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        # Professional audit trail
        logging.FileHandler("webatlas_pipeline.log"),
        # Real-time terminal feedback
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="WebAtlas - Build an interactive link graph"
    )
    parser.add_argument(
        "--xlsx", nargs=2, metavar=("INTERNAL", "OUTLINKS"), required=True
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
        logger.info(
            f"Importing data from {internal_xlsx} and {outlinks_xlsx}.."
        )
        importer = ScreamingFrogImport().load(internal_xlsx, outlinks_xlsx)
        logger.info(f"Data imported successfully. Found {len(
            importer.nodes)} nodes and {len(
            importer.edges)} edges")

        # Build Graph (Pass importer directly to leverage GraphBuilder.__init__)
        logger.info("Initialising GraphBuilder and mapping XPaths..")
        graph = GraphBuilder(sf_importer=importer)

        # Generate Interactive HTML (Replacing write_dot)
        logger.info(f"Generating Interactive Mothball: {output_file}")
        logger.info(
            "Note: Stabilisation physics may take 10 secs for large crawls."
        )
        graph.build_interactive_graph(output_file)

        logger.info(f"Pipeline completed!  Output saved to: {output_file}")

    except (
        OSError,
        ValueError,
        KeyError,
        AttributeError,
        RuntimeError,
        TypeError,
    ):
        logger.exception("Pipeline Failed:")
        sys.exit(1)


if __name__ == "__main__":
    main()
