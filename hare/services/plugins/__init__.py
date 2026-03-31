from hare.services.plugins.plugin_types import PluginConfig, PluginManifest
from hare.services.plugins.plugin_operations import (
    find_plugin_in_settings,
    install_plugin,
    remove_plugin,
)
from hare.services.plugins.plugin_installation_manager import (
    perform_background_plugin_installations,
)
