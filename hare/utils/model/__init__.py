from hare.utils.model.model_full import (
    get_main_loop_model, get_default_opus_model,
    get_default_sonnet_model, get_default_haiku_model,
    get_small_fast_model, get_runtime_main_loop_model,
    get_user_specified_model_setting, get_best_model,
)

# Re-export from old location for backward compat
try:
    from hare.utils.model_strings import normalize_model_string_for_api
except ImportError:
    def normalize_model_string_for_api(model: str) -> str:
        """Normalize a model string for API use."""
        model = model.strip()
        if model.endswith("[1m]"):
            model = model[:-4]
        return model
