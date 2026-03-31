"""
Hook system for pre/post tool execution.

Port of: src/utils/hooks/
"""

from hare.utils.hooks.hook_events import HookEvent, HOOK_EVENTS
from hare.utils.hooks.hook_registry import AsyncHookRegistry, get_hook_registry
from hare.utils.hooks.file_changed_watcher import FileChangedWatcher
