"""
Bash/shell command parsing and analysis.

Port of: src/utils/bash/
"""

from hare.utils.bash.parser import parse_command, ParsedCommand
from hare.utils.bash.shell_quoting import shell_quote, shell_join
from hare.utils.bash.commands import split_command, get_command_name
