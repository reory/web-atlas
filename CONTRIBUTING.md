# Contributing to WebAtlas 🕸️

Thank you for considering contributing to **WebAtlas**! We appreciate your help in making this interactive SEO link visualizer more robust and insightful.

---

## 📑 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#-how-can-i-contribute)
- [Data Privacy](#-data-privacy)
- [Development Setup](#-development-setup)
- [Running Tests](#-testing)
- [Project Architecture & Style Guide](#-project-architecture--style-guide)

---

## Code of Conduct
Be kind, be professional, and let's build something cool together.

---

## 🛠️ How Can I Contribute?

### 🐛 Reporting Bugs
If you encounter unexpected errors or issues while parsing exports or rendering graphs:
* Check the **Issues** tab to see if the bug has already been reported.
* If not, open a new issue. Please include:
    * Your Screaming Frog version.
    * A screenshot of the error (if possible).
    * A brief description of what you were doing when the application broke.

### ✨ Suggesting Enhancements
We are always looking for ways to make the graph more insightful! Check our [Roadmap Features](README.md#-roadmap-features) section before proposing new features. Ideas welcomed include:
* Improving status code rendering and error handling.
* Enhancing PageRank node scaling calculations.
* Refactoring inline JavaScript/HTML templates into dedicated assets.

### 🛠️ Pull Requests
1. **Fork** the repo and create your branch from `main`.
2. If you've added code that should be tested, add unit tests!
3. Ensure the documentation (`README.md`) is updated if you change how the script runs.
4. Issue that Pull Request!

---

## 🔒 Data Privacy
When contributing examples or bug reports, **please redact any sensitive client URLs** or internal data. We recommend using `example.com` for all test data.

---

## 🚀 Development Setup

To set up your local development environment to run and test the interactive SEO link visualiser:

1. **Clone and Navigate** into your local repository clone:
   ```bash
   git clone https://github.com/reory/web-atlas.git
   cd web-atlas
   ```

2. **Install Dependencies**:
   ```bash
   pip install pyvis networkX openpyxl
   ```

3. **Run the Application**: Export your internal HTML reports and outlinks from Screaming Frog, then execute the CLI entry point:
   ```bash
   python main.py --xlsx internal.xlsx All_Outlinks.xlsx atlas.html
   ```
   *Open `atlas.html` in any modern web browser to explore your site's architecture.*

---

## 🧪 Testing

The project includes a `pytest` suite to validate graph initialisation and data integrity. Run the following command before submitting a pull request to ensure the "mothball" logic and XPath mapping function correctly:

```bash
pytest
```

---

## 📏 Project Architecture & Style Guide
* **Python Standards**: Follow PEP 8 guidelines for clean, readable code.
* **Core Package Layout**: Keep responsibilities organised across the `webatlas/` package:
  * `sf_import.py`: Screaming Frog XLSX importer
  * `graph_builder/`: NetworkX graph construction and SEO logic (`builder.py`, `constants.py`, `html_injector.py`, `network_ops.py`, `pyvis_config.py`)
  * `tests/`: Pytest suite (`test_builder.py`, `test_html_injector.py`, `test_network_ops.py`, `test_sf_imports.py`)