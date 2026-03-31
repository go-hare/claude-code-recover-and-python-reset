"""
Notebook Edit Tool - edit Jupyter notebook cells.

Port of: src/tools/NotebookEditTool/NotebookEditTool.ts

Supports:
- replace: Replace cell content
- insert: Insert new cell after specified position
- delete: Delete a cell
"""

from __future__ import annotations

import json
import os
import random
import string
from typing import Any, Optional

TOOL_NAME = "NotebookEdit"
DESCRIPTION = "Edit Jupyter notebook cells (.ipynb files)"
PROMPT = """Use this tool to edit a jupyter notebook cell. Use ONLY this tool to edit notebooks.

This tool supports editing existing cells and creating new cells:
- If you need to edit an existing cell, set edit_mode to 'replace' and provide the cell_id.
- If you need to create a new cell, set edit_mode to 'insert' and provide the cell_id of the cell after which to insert.
- If you need to delete a cell, set edit_mode to 'delete' and provide the cell_id.

Cell IDs can be found by reading the notebook file first."""


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "notebook_path": {
                "type": "string",
                "description": "Absolute path to the Jupyter notebook file",
            },
            "cell_id": {
                "type": "string",
                "description": "The ID of the cell to edit, or the cell after which to insert",
            },
            "new_source": {
                "type": "string",
                "description": "The new source content for the cell",
            },
            "cell_type": {
                "type": "string",
                "enum": ["code", "markdown"],
                "description": "Cell type (required for insert mode)",
            },
            "edit_mode": {
                "type": "string",
                "enum": ["replace", "insert", "delete"],
                "description": "Edit mode: replace, insert, or delete",
            },
        },
        "required": ["notebook_path", "new_source"],
    }


async def call(
    notebook_path: str,
    new_source: str,
    cell_id: Optional[str] = None,
    cell_type: Optional[str] = None,
    edit_mode: str = "replace",
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute notebook edit operation."""
    full_path = os.path.abspath(notebook_path)

    if not full_path.endswith(".ipynb"):
        return _error("File must be a Jupyter notebook (.ipynb)")

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        notebook = json.loads(content)
    except FileNotFoundError:
        return _error("Notebook file does not exist")
    except json.JSONDecodeError:
        return _error("Notebook is not valid JSON")

    cells = notebook.get("cells", [])

    # Find cell index
    cell_index = _find_cell_index(cells, cell_id)

    if edit_mode == "delete":
        if cell_index is None or cell_index >= len(cells):
            return _error(f"Cell {cell_id} not found")
        cells.pop(cell_index)

    elif edit_mode == "insert":
        if not cell_type:
            return _error("cell_type is required for insert mode")
        insert_at = (cell_index + 1) if cell_index is not None else 0
        new_cell = _make_cell(new_source, cell_type, notebook)
        cells.insert(insert_at, new_cell)

    else:  # replace
        if cell_index is None or cell_index >= len(cells):
            return _error(f"Cell {cell_id} not found")
        target = cells[cell_index]
        target["source"] = new_source
        if target.get("cell_type") == "code":
            target["execution_count"] = None
            target["outputs"] = []
        if cell_type and cell_type != target.get("cell_type"):
            target["cell_type"] = cell_type

    # Write back
    updated = json.dumps(notebook, indent=1, ensure_ascii=False)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(updated)

    language = notebook.get("metadata", {}).get("language_info", {}).get("name", "python")

    return {
        "new_source": new_source,
        "cell_type": cell_type or "code",
        "language": language,
        "edit_mode": edit_mode,
        "cell_id": cell_id,
        "notebook_path": full_path,
        "original_file": content,
        "updated_file": updated,
    }


def _find_cell_index(cells: list, cell_id: Optional[str]) -> Optional[int]:
    """Find cell by ID or numeric index."""
    if cell_id is None:
        return None
    for i, cell in enumerate(cells):
        if cell.get("id") == cell_id:
            return i
    # Try cell-N format
    if cell_id.startswith("cell-"):
        try:
            return int(cell_id[5:])
        except ValueError:
            pass
    try:
        return int(cell_id)
    except ValueError:
        pass
    return None


def _make_cell(source: str, cell_type: str, notebook: dict) -> dict:
    """Create a new notebook cell."""
    nbformat = notebook.get("nbformat", 4)
    nbformat_minor = notebook.get("nbformat_minor", 0)

    cell: dict[str, Any] = {
        "cell_type": cell_type,
        "source": source,
        "metadata": {},
    }

    if nbformat > 4 or (nbformat == 4 and nbformat_minor >= 5):
        cell["id"] = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []

    return cell


def _error(message: str) -> dict[str, Any]:
    return {"error": message, "new_source": "", "cell_type": "code",
            "language": "python", "edit_mode": "replace",
            "notebook_path": "", "original_file": "", "updated_file": ""}
