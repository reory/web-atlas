# 🕸️ WebAtlas: Interactive SEO Link Visualizer
![Last Commit](https://img.shields.io/github/last-commit/reory/web-atlas?cacheSeconds=60)
![Repo Size](https://img.shields.io/github/repo-size/reory/web-atlas?cacheSeconds=60)
![License](https://img.shields.io/badge/License-MIT-green)

[![PyVis](https://img.shields.io/badge/PyVis-0.3.2-blue?style=flat-square&logo=python)](https://pypi.org/project/pyvis/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.6.1-orange?style=flat-square&logo=python)](https://pypi.org/project/networkx/)
[![Openpyxl](https://img.shields.io/badge/Openpyxl-3.1.5-green?style=flat-square&logo=microsoft-excel)](https://pypi.org/project/openpyxl/)

Interactive SEO Link Visualizer for Screaming Frog Exports.
WebAtlas is a Python-based technical SEO tool that transforms flat Screaming Frog Excel exports into dynamic, interactive network graphs. It allows SEOs to visualize internal linking structures, identify crawl depth issues, and discover topical silos that are invisible in standard spreadsheets.

---

# 📹 Demo video
https://github.com/user-attachments/assets/64bebdd6-d904-49d4-b805-b4264af6d759

---

# 🚀 The Core Problem & Solution

- The "Graphviz Nightmare"Initially, this project attempted to use Graphviz (the industry standard for diagramming). However, I encountered a major hurdle:
- Graphviz is designed for Hierarchical Trees (like org charts).
- Websites are Non-Linear Networks (where any page can link to any other page).
When Graphviz tries to force a website into a tree structure, it results in an "infinite vertical strip" that is impossible to read or navigate.
- The "PyVis" Evolution
I pivoted to NetworkX (for the mathematical graph logic) and PyVis (for the browser-based visualization).
- Physics-Based Layout: Instead of a static image, I now have a "force-directed" graph. Nodes push each other away until they find space, naturally "untangling" the website's structure.
- Interactivity: Users can zoom, drag nodes, and hover over elements to see hidden metadata.

---

# ✨ Key Features
- Interactive Hover Tooltips: Nodes are labeled with short, clean URLs (slugs), but hovering over them reveals the full URL and the exact XPath/Link Position where the link was found.
- Noise Reduction: Automatically filters out non-hyperlinks (Images, CSS, JS, etc.) to focus specifically on the "Internal Link Ecosystem.
- Performance Optimized: Uses the Barnes-Hut physics engine and stabilization iterations to ensure that even large sites (the "Mothball" effect) load quickly in the browser.
- Dark - Mode Visualization: Designed with a high-contrast dark theme for better visibility of complex link paths.

---

# 🛠️ Installation
Ensure you have Python 3.10+ installed.
## Clone the repository:
```Bash
git clone https://github.com/reory/web-atlas.git
cd web-atlas
```
## Install dependencies:
```Bash
pip install pyvis networkx openpyxl
```
## 📂 Usage
- To generate your interactive map, you need two exports from Screaming Frog (XLSX format):Internal (All HTML pages)All Outlinks (The massive list of every link found)
- Run the following command:
PowerShell
```bash
python main.py --xlsx internal.xlsx All_Outlinks.xlsx atlas.html
```
- Open atlas.html in any modern web browser to explore your site's architecture.

---

# Tech Stack
* **PyVis** is a Python library built specifically for creating interactive network graphs that run in a web browser.
* **Networkx** Performs advanced SEO analysis, such as identifying "Orphan Pages" (nodes with no incoming edges) or calculating "PageRank" to see which pages hold the most authority.
* **OpenPyxl** is a library used to read and write Excel (.xlsx) files.

---

# 📁 Project Structure
```
web-atlas/
├── webatlas/                 # Core package
│   ├── __init__.py
│   ├── sf_import.py          # Screaming Frog XLSX importer
│   ├── graph_builder.py      # NetworkX graph construction + SEO logic
│                             # PyVis HTML visualization
│
├── lib/                      # Additional assets or helper modules
│   └── ...                   
│
├── tests/                    # Pytest suite
│   ├── test_graph_builder.py
│   
│
├── main.py                   # CLI entry point
├── README.md                 # Project documentation
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE.md                # MIT license
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Build + metadata config
├── demo.mp4                  # Demo video
```

---

# 🧠 Why this Architecture?
- Component Why I chose it
- Openpyxl Allows us to read massive Excel files directly without needing a database
- NetworkX The "brain" of the project. It handles the complex math of linking thousands of nodes.
- PyVis The "beauty." It turns the math into an interactive HTML/JavaScript experience that runs in any browser.

---

# 🕵️‍♂️ How to Read the "Mothball"
- When you first open your graph, you might see a dense cluster (a "mothball"). Here’s how to audit it:
- The Core: The center of the ball usually contains your Header and Footer links.
- The Planets: Small clusters orbiting the main ball are often your Blog categories or Service silos.
- The Drifters: Nodes floating far away with only one connection are "Deep Pages" or near-orphans that need better internal linking to rank.

- Built for SEOs who want to see their data, not just read it.

---

# 🧪 Tests
- The project includes a Pytest suite to validate graph initialization and data integrity. 
- Run python -m pytest tests/ to ensure the "mothball" logic and XPath mapping are functioning correctly before deployment.

---

# 🛣️ Roadmap Features

- [ ]🚦Status Code Color-Coding
Right now, every node is blue. In a real audit, you want the "danger" to pop out visually.

The Feature: Modify sf_import.py to pull the Status Code column from the "Internal" export.

The Visual: * Green: 200 OK

Yellow: 301/302 Redirects

Red: 404/500 Errors

- [ ]🎈 Node Scaling by "Internal PageRank"

The Feature: Use NetworkX to calculate the pagerank or in_degree (number of incoming links) for every node.

The Visual: Important pages with lots of "Link Juice" become large, dominant circles, while deep, unimportant pages stay tiny.

- [ ]📂 Folder-Based "Silo" Grouping
Websites are usually organized by folders (e.g., /blog/, /products/, /services/).

Use Python's string splitting to group URLs by their first subfolder.

The Visual: Add a "Legend" or use different colors for different folders. You can even add a toggle to "Hide all Blog posts" to see only the core service architecture.

---

* **Built by Roy Peters** 😁
[![LinkedIn](https://img.shields.io/badge/LinkedIn-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/roy-p-74980b382/)