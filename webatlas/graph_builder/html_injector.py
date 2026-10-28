"""Manages file output and HTML/JS template post-processing."""

import json
import logging

from pyvis.network import Network

logger = logging.getLogger(__name__)


def inject_custom_html(
    net: Network, 
    output_file: str, 
    node_colors_dict: dict[str, str],
    silos_dict: dict[str, list[str]]
) -> None:
    """
    Save network HTML and inject physics freeze script,
    colour dictionaries, and toolbar UI with density sliders.
    """
    
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
        
        # Interactive Silo Toolbar HTML & JavaScript Control with Full-Page Dark Mode
        silo_toolbar_html = """
        <div id="silo-toolbar" style="position: absolute; top: 15px; left: 15px; z-index: 1000; background: rgba(255, 255, 255, 0.95); padding: 10px 14px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); font-family: sans-serif; width: 320px; transition: background 0.3s, color 0.3s;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong id="toolbar-title" style="font-size: 12px; color: #333;">Graph Controls & Filters:</strong>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <button id="theme-toggle-btn" onclick="toggleDarkMode()" style="padding: 2px 6px; font-size: 11px; cursor: pointer; background: #333; color: #fff; border: none; border-radius: 4px;">🌙 Dark</button>
                    <div style="font-size: 10px; display: flex; gap: 4px;">
                        <span style="color: #2ecc71; font-weight: bold;">■ 200</span>
                        <span style="color: #f1c40f; font-weight: bold;">■ Redirect</span>
                        <span style="color: #e74c3c; font-weight: bold;">■ Error</span>
                    </div>
                </div>
            </div>

            <!-- Density Sliders -->
            <div style="margin-bottom: 10px; font-size: 11px;" id="slider-labels-container">
                <label style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                    <span>Min Degree: <strong id="deg-val">0</strong></span>
                </label>
                <input type="range" id="deg-slider" min="0" max="50" value="0" style="width: 100%; cursor: pointer;" oninput="updateGraphFilters()">
                
                <label style="display: flex; justify-content: space-between; margin-top: 6px; margin-bottom: 2px;">
                    <span>Min PageRank: <strong id="pr-val">0.0000</strong></span>
                </label>
                <input type="range" id="pr-slider" min="0" max="100" value="0" style="width: 100%; cursor: pointer;" oninput="updateGraphFilters()">
            </div>

            <div id="silo-heading" style="font-size: 11px; font-weight: bold; color: #333; margin-bottom: 4px;">Folder Silos:</div>
            <div id="silo-buttons" style="display: flex; flex-wrap: wrap; gap: 4px; max-height: 130px; overflow-y: auto; padding-right: 4px;">
                <button onclick="filterSilo('ALL', this)" style="padding: 3px 8px; font-size: 10px; cursor: pointer; background: #333; color: #fff; border: none; border-radius: 4px;">All</button>
            </div>
        </div>
        <script type="text/javascript">
            let currentActiveSilo = 'ALL';
            let maxGraphPr = 0.1;
            let isDarkMode = false;

            window.addEventListener("load", function() {
                if (typeof nodes !== "undefined") {
                    const allNodes = nodes.get();
                    allNodes.forEach(n => {
                        if (n.pagerank && n.pagerank > maxGraphPr) {
                            maxGraphPr = n.pagerank;
                        }
                    });
                }

                if (typeof silosMap !== "undefined" && document.getElementById("silo-buttons")) {
                    const container = document.getElementById("silo-buttons");
                    Object.keys(silosMap).forEach(silo => {
                        const btn = document.createElement("button");
                        btn.innerText = silo;
                        btn.style.padding = "3px 8px";
                        btn.style.fontSize = "10px";
                        btn.style.cursor = "pointer";
                        btn.style.background = isDarkMode ? "#444" : "#e0e0e0";
                        btn.style.color = isDarkMode ? "#fff" : "#333";
                        btn.style.border = "none";
                        btn.style.borderRadius = "4px";
                        btn.onclick = () => filterSilo(silo, btn);
                        container.appendChild(btn);
                    });
                }
            });

            function toggleDarkMode() {
                isDarkMode = !isDarkMode;
                const toolbar = document.getElementById("silo-toolbar");
                const toggleBtn = document.getElementById("theme-toggle-btn");
                const toolbarTitle = document.getElementById("toolbar-title");
                const siloHeading = document.getElementById("silo-heading");
                
                // Target HTML, Body, and PyVis network canvas container
                const html = document.documentElement;
                const body = document.body;
                const networkDiv = document.getElementById("mynetwork") || document.querySelector(".vis-network");

                if (isDarkMode) {
                    html.style.backgroundColor = "#1a1a1a";
                    body.style.backgroundColor = "#1a1a1a";
                    if (networkDiv) networkDiv.style.backgroundColor = "#1a1a1a";
                    
                    toolbar.style.background = "rgba(30, 30, 30, 0.95)";
                    toolbar.style.color = "#ffffff";
                    toolbarTitle.style.color = "#ffffff";
                    siloHeading.style.color = "#ffffff";
                    toggleBtn.innerText = "☀️ Light";
                    toggleBtn.style.background = "#ffffff";
                    toggleBtn.style.color = "#000000";
                } else {
                    html.style.backgroundColor = "#ffffff";
                    body.style.backgroundColor = "#ffffff";
                    if (networkDiv) networkDiv.style.backgroundColor = "#ffffff";
                    
                    toolbar.style.background = "rgba(255, 255, 255, 0.95)";
                    toolbar.style.color = "#333333";
                    toolbarTitle.style.color = "#333333";
                    siloHeading.style.color = "#333333";
                    toggleBtn.innerText = "🌙 Dark";
                    toggleBtn.style.background = "#333333";
                    toggleBtn.style.color = "#ffffff";
                }

                // Update unselected button backgrounds for contrast
                const allButtons = document.querySelectorAll("#silo-buttons button");
                allButtons.forEach(b => {
                    const isActive = b.innerText === currentActiveSilo || (currentActiveSilo === 'ALL' && b.innerText === 'All');
                    if (!isActive) {
                        b.style.background = isDarkMode ? "#444444" : "#e0e0e0";
                        b.style.color = isDarkMode ? "#ffffff" : "#333333";
                    }
                });
            }

            function filterSilo(targetSilo, clickedBtn) {
                currentActiveSilo = targetSilo;

                const allButtons = document.querySelectorAll("#silo-buttons button");
                allButtons.forEach(b => {
                    b.style.background = isDarkMode ? "#444444" : "#e0e0e0";
                    b.style.color = isDarkMode ? "#ffffff" : "#333333";
                });
                if (clickedBtn) {
                    clickedBtn.style.background = isDarkMode ? "#2563eb" : "#333333";
                    clickedBtn.style.color = "#ffffff";
                }
                updateGraphFilters(); 
            }

            function updateGraphFilters() {
                if (typeof nodes === "undefined") return;

                const minDeg = parseInt(document.getElementById("deg-slider").value) || 0;

                // Aggressive quartic mapping for PageRank slider
                const sliderPercent = (parseFloat(document.getElementById("pr-slider").value) || 0) / 100.0;
                const minPr = Math.pow(sliderPercent, 12) * maxGraphPr;

                document.getElementById("deg-val").innerText = minDeg;
                document.getElementById("pr-val").innerText = minPr.toFixed(12);

                const allNodes = nodes.get();
                const targetList = silosMap[currentActiveSilo] || [];

                const updatedNodes = allNodes.map(node => {
                    const nodeDeg = node.degree || 0;
                    const nodePr = node.pagerank || 0;

                    let siloMatch = true;
                    if (currentActiveSilo !== 'ALL') {
                        siloMatch = targetList.includes(node.id) || targetList.some(item => node.id.includes(item) || item.includes(node.id));
                    }

                    const degreeMatch = nodeDeg >= minDeg;
                    const prMatch = nodePr >= minPr;
                    
                    node.hidden = !(siloMatch && degreeMatch && prMatch);
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