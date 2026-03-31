"""
Permission system.

Port of: src/utils/permissions/
"""

from hare.utils.permissions.filesystem import (
    check_path_safety_for_auto_edit,
    check_read_permission_for_tool,
    check_write_permission_for_tool,
    matching_rule_for_input,
    path_in_working_path,
    path_in_allowed_working_path,
    generate_suggestions,
    DANGEROUS_FILES,
    DANGEROUS_DIRECTORIES,
)
from hare.utils.permissions.shell_rule_matching import (
    match_wildcard_pattern,
    parse_permission_rule,
    has_wildcards,
)
from hare.utils.permissions.permission_mode import (
    permission_mode_title,
    permission_mode_from_string,
    is_default_mode,
    to_external_permission_mode,
)
