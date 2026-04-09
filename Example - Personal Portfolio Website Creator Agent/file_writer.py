"""
File writing utilities for the portfolio builder.

Saves generated HTML / CSS / JS files to the outputs/ directory and
packages them into a timestamped ZIP archive for download.
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path


# Absolute path to the outputs directory (relative to this file's package root)
OUTPUTS_DIR = Path(__file__).resolve().parent / "outputs"


def ensure_outputs_dir() -> Path:
    """Create the outputs directory if it does not exist and return it."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def write_portfolio_files(files: dict) -> Path:
    """
    Write the generated website files to a timestamped sub-directory and
    bundle them into a ZIP archive.

    Args:
        files: dict with keys "index.html", "style.css", "main.js"
               and string content as values.

    Returns:
        Path to the created ZIP file.
    """
    outputs_dir = ensure_outputs_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    portfolio_dir = outputs_dir / f"portfolio_{timestamp}"
    portfolio_dir.mkdir(parents=True, exist_ok=True)

    # Write individual files
    for filename, content in files.items():
        # Sanitise filename – only allow safe characters
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename:
            # Skip files with path-traversal attempts
            continue
        file_path = portfolio_dir / safe_name
        file_path.write_text(content, encoding="utf-8")

    # Create ZIP archive
    zip_path = outputs_dir / f"portfolio_{timestamp}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in files:
            safe_name = Path(filename).name
            file_path = portfolio_dir / safe_name
            if file_path.exists():
                zf.write(file_path, arcname=safe_name)

    return zip_path


def list_output_zips() -> list[Path]:
    """Return a sorted list of all ZIP archives in the outputs directory."""
    outputs_dir = ensure_outputs_dir()
    return sorted(outputs_dir.glob("portfolio_*.zip"), reverse=True)
