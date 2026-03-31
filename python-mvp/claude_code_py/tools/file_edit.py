from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from claude_code_py.engine.context import ReadFileState, ToolContext
from claude_code_py.engine.models import ToolRunResult
from claude_code_py.tools.base import Tool
from claude_code_py.tools._text_files import (
    apply_edit_to_content,
    find_actual_string,
    preserve_quote_style,
    read_text_file,
    write_text_file,
)


class FileEditTool(Tool):
    name = "Edit"
    description = "A tool for editing files"
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to modify",
            },
            "old_string": {
                "type": "string",
                "description": "The text to replace",
            },
            "new_string": {
                "type": "string",
                "description": "The text to replace it with (must be different from old_string)",
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences of old_string (default false)",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    async def run(
        self,
        tool_input: Mapping[str, Any],
        context: ToolContext,
    ) -> ToolRunResult:
        path = context.resolve_path(str(tool_input["file_path"]))
        old_string = str(tool_input["old_string"])
        new_string = str(tool_input["new_string"])
        replace_all = bool(tool_input.get("replace_all", False))

        if old_string == new_string:
            return ToolRunResult(
                content="No changes to make: old_string and new_string are exactly the same.",
                is_error=True,
            )

        stored = context.read_file_state.get(str(path))
        if not path.exists():
            if old_string == "":
                original = ""
                file_data = None
            else:
                return ToolRunResult(
                    content=f"File does not exist: {path}",
                    is_error=True,
                )
        else:
            file_data = read_text_file(path)
            original = file_data.content
            allow_empty_file_write = old_string == "" and not original.strip()
            if old_string == "" and original.strip():
                return ToolRunResult(
                    content="Cannot create new file - file already exists.",
                    is_error=True,
                )
            if not allow_empty_file_write:
                if path.suffix.lower() == ".ipynb":
                    return ToolRunResult(
                        content="File is a Jupyter Notebook. Use the NotebookEdit tool to edit this file.",
                        is_error=True,
                    )
                if stored is None or stored.is_partial_view:
                    return ToolRunResult(
                        content="File has not been read yet. Read it first before writing to it.",
                        is_error=True,
                    )
                if path.stat().st_mtime > stored.timestamp and original != stored.content:
                    return ToolRunResult(
                        content="File has been modified since read, either by the user or by a linter. Read it again before attempting to write it.",
                        is_error=True,
                    )

        if old_string:
            actual_old_string = find_actual_string(original, old_string)
            if actual_old_string is None:
                return ToolRunResult(
                    content=f"String to replace not found in file.\nString: {old_string}",
                    is_error=True,
                )
            occurrences = original.count(actual_old_string)
            if occurrences > 1 and not replace_all:
                return ToolRunResult(
                    content=(
                        f"Found {occurrences} matches of the string to replace, but replace_all is false. "
                        "To replace all occurrences, set replace_all to true. To replace only one occurrence, please provide more context to uniquely identify the instance.\n"
                        f"String: {old_string}"
                    ),
                    is_error=True,
                )
            actual_new_string = preserve_quote_style(
                old_string,
                actual_old_string,
                new_string,
            )
            updated = apply_edit_to_content(
                original,
                actual_old_string,
                actual_new_string,
                replace_all=replace_all,
            )
        else:
            updated = new_string

        if updated == original:
            return ToolRunResult(
                content="Original and edited file match exactly. Failed to apply edit.",
                is_error=True,
            )

        if file_data is None:
            write_text_file(path, updated)
        else:
            write_text_file(
                path,
                updated,
                encoding=file_data.encoding,
                bom=file_data.bom,
                line_ending=file_data.line_ending,
            )
        context.read_file_state[str(path)] = ReadFileState(
            content=updated,
            timestamp=path.stat().st_mtime,
            offset=None,
            limit=None,
        )
        return ToolRunResult(content=f"The file {path} has been updated successfully.")
