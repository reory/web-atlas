"""Contains configuration constants and color-coding rules"""

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