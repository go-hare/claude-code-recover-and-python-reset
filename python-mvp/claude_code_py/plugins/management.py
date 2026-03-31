from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse as urllib_parse_url
from urllib.request import urlopen
from uuid import uuid4


@dataclass(slots=True)
class PluginRecord:
    name: str
    path: Path
    scope: str
    disabled: bool


@dataclass(slots=True)
class ValidationMessage:
    path: str
    message: str
    code: str | None = None


@dataclass(slots=True)
class ValidationResult:
    success: bool
    errors: list[ValidationMessage]
    warnings: list[ValidationMessage]
    file_path: str
    file_type: str


@dataclass(slots=True)
class AddMarketplaceResult:
    name: str
    already_materialized: bool
    resolved_source: dict[str, Any]


_SSH_SOURCE_RE = re.compile(r"^([a-zA-Z0-9._-]+@[^:]+:.+?(?:\.git)?)(#(.+))?$")
_URL_WITH_FRAGMENT_RE = re.compile(r"^([^#]+)(#(.+))?$")
_GITHUB_URL_RE = re.compile(r"^/([^/]+/[^/]+?)(/|\.git|$)")
_REPO_WITH_REF_RE = re.compile(r"^([^#@]+)(?:[#@](.+))?$")


def discover_plugin_records(cwd: Path, config_home: Path) -> list[PluginRecord]:
    records: list[PluginRecord] = []
    locations = [
        ("project", cwd / ".claude" / "plugins"),
        ("user", config_home / "plugins"),
    ]
    for scope, directory in locations:
        if not directory.exists():
            continue
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir():
                continue
            manifest = _read_manifest(entry / "plugin.json")
            plugin_name = str(manifest.get("name") or entry.name).strip() or entry.name
            records.append(
                PluginRecord(
                    name=plugin_name,
                    path=entry,
                    scope=scope,
                    disabled=bool(manifest.get("disabled", False)),
                )
            )
    return records


def get_plugins_directory(config_home: Path) -> Path:
    return config_home / "plugins"


def get_known_marketplaces_file(config_home: Path) -> Path:
    return get_plugins_directory(config_home) / "known_marketplaces.json"


def get_marketplaces_cache_dir(config_home: Path) -> Path:
    return get_plugins_directory(config_home) / "marketplaces"


def load_known_marketplaces_config(config_home: Path) -> dict[str, dict[str, Any]]:
    config_file = get_known_marketplaces_file(config_home)
    if not config_file.exists():
        return {}
    parsed = json.loads(config_file.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Marketplace configuration file is corrupted")
    return {
        str(name): dict(entry)
        for name, entry in parsed.items()
        if isinstance(name, str) and isinstance(entry, dict)
    }


def save_known_marketplaces_config(
    config_home: Path,
    config: dict[str, dict[str, Any]],
) -> None:
    plugins_dir = get_plugins_directory(config_home)
    plugins_dir.mkdir(parents=True, exist_ok=True)
    get_known_marketplaces_file(config_home).write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_marketplace_input(
    value: str,
    cwd: Path,
) -> dict[str, Any] | None:
    trimmed = value.strip()
    if not trimmed:
        return None

    ssh_match = _SSH_SOURCE_RE.match(trimmed)
    if ssh_match is not None:
        url = ssh_match.group(1)
        ref = ssh_match.group(3)
        return {"source": "git", "url": url, **({"ref": ref} if ref else {})}

    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        fragment_match = _URL_WITH_FRAGMENT_RE.match(trimmed)
        url_without_fragment = (
            fragment_match.group(1) if fragment_match is not None else trimmed
        )
        ref = fragment_match.group(3) if fragment_match is not None else None
        if url_without_fragment.endswith(".git") or "/_git/" in url_without_fragment:
            return {
                "source": "git",
                "url": url_without_fragment,
                **({"ref": ref} if ref else {}),
            }
        try:
            parsed_url = urllib_parse_url(url_without_fragment)
        except ValueError:
            return {"source": "url", "url": url_without_fragment}
        if parsed_url.hostname in {"github.com", "www.github.com"}:
            repo_match = _GITHUB_URL_RE.match(parsed_url.path)
            if repo_match is not None:
                git_url = (
                    url_without_fragment
                    if url_without_fragment.endswith(".git")
                    else f"{url_without_fragment}.git"
                )
                return {
                    "source": "git",
                    "url": git_url,
                    **({"ref": ref} if ref else {}),
                }
        return {"source": "url", "url": url_without_fragment}

    local_source = _parse_local_marketplace_path(trimmed, cwd)
    if local_source is not None:
        return local_source

    if "/" in trimmed and not trimmed.startswith("@"):
        if ":" in trimmed:
            return None
        fragment_match = _REPO_WITH_REF_RE.match(trimmed)
        repo = fragment_match.group(1) if fragment_match is not None else trimmed
        ref = fragment_match.group(2) if fragment_match is not None else None
        return {"source": "github", "repo": repo, **({"ref": ref} if ref else {})}

    return None


def add_marketplace_source(
    source: dict[str, Any],
    cwd: Path,
    config_home: Path,
) -> AddMarketplaceResult:
    resolved_source = _resolve_marketplace_source(source, cwd)
    existing = load_known_marketplaces_config(config_home)
    for existing_name, existing_entry in existing.items():
        if existing_entry.get("source") == resolved_source:
            return AddMarketplaceResult(
                name=existing_name,
                already_materialized=True,
                resolved_source=resolved_source,
            )

    name, install_location = _materialize_marketplace_source(
        resolved_source,
        config_home,
    )
    config = load_known_marketplaces_config(config_home)
    previous = config.get(name)
    if previous is not None:
        _cleanup_old_marketplace_cache(previous, install_location, config_home)
    config[name] = {
        "source": resolved_source,
        "installLocation": str(install_location),
        "lastUpdated": _now_iso8601(),
    }
    save_known_marketplaces_config(config_home, config)
    return AddMarketplaceResult(
        name=name,
        already_materialized=False,
        resolved_source=resolved_source,
    )


def remove_marketplace_source(name: str, config_home: Path) -> None:
    config = load_known_marketplaces_config(config_home)
    if name not in config:
        raise ValueError(f"Marketplace '{name}' not found")

    entry = config.pop(name)
    save_known_marketplaces_config(config_home, config)

    install_location = Path(str(entry.get("installLocation", "")))
    cache_dir = get_marketplaces_cache_dir(config_home).resolve()
    if install_location.exists():
        resolved_install = install_location.resolve()
        if resolved_install == cache_dir or str(resolved_install).startswith(
            str(cache_dir) + os.sep
        ):
            if resolved_install.is_dir():
                shutil.rmtree(resolved_install, ignore_errors=True)
            else:
                resolved_install.unlink(missing_ok=True)

    shutil.rmtree(cache_dir / name, ignore_errors=True)
    (cache_dir / f"{name}.json").unlink(missing_ok=True)


def refresh_marketplace(name: str, config_home: Path) -> None:
    config = load_known_marketplaces_config(config_home)
    entry = config.get(name)
    if entry is None:
        available = ", ".join(sorted(config))
        raise ValueError(
            f"Marketplace '{name}' not found. Available marketplaces: {available}"
        )

    source = dict(entry.get("source") or {})
    if not source:
        raise ValueError(f"Marketplace '{name}' has no source")

    install_location = Path(str(entry.get("installLocation", "")))
    refreshed_name, refreshed_location = _refresh_marketplace_source(
        source,
        install_location,
        config_home,
    )
    if refreshed_name != name:
        config.pop(name, None)
    config[refreshed_name] = {
        "source": source,
        "installLocation": str(refreshed_location),
        "lastUpdated": _now_iso8601(),
    }
    save_known_marketplaces_config(config_home, config)


def refresh_all_marketplaces(config_home: Path) -> int:
    config = load_known_marketplaces_config(config_home)
    names = sorted(config)
    for name in names:
        try:
            refresh_marketplace(name, config_home)
        except Exception:
            continue
    return len(names)


def format_known_marketplaces(config: dict[str, dict[str, Any]]) -> str:
    names = sorted(config)
    if not names:
        return "No marketplaces configured"

    lines = ["Configured marketplaces:", ""]
    for name in names:
        lines.append(f"  - {name}")
        source = config[name].get("source")
        if isinstance(source, dict):
            lines.append(f"    Source: {_format_marketplace_source(source)}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _parse_local_marketplace_path(
    value: str,
    cwd: Path,
) -> dict[str, Any] | None:
    is_windows_path = os.name == "nt" and (
        value.startswith(".\\")
        or value.startswith("..\\")
        or re.match(r"^[a-zA-Z]:[/\\]", value) is not None
    )
    if not (
        value.startswith("./")
        or value.startswith("../")
        or value.startswith("/")
        or value.startswith("~")
        or is_windows_path
    ):
        return None

    expanded = value
    if expanded.startswith("~"):
        expanded = str(Path.home()) + expanded[1:]
    resolved = Path(expanded)
    if not resolved.is_absolute():
        resolved = (cwd / resolved).resolve()
    else:
        resolved = resolved.resolve()

    if resolved.is_file():
        if resolved.suffix.lower() != ".json":
            raise ValueError(
                "File path must point to a .json file (marketplace.json), "
                f"but got: {resolved}"
            )
        return {"source": "file", "path": str(resolved)}
    if resolved.is_dir():
        return {"source": "directory", "path": str(resolved)}
    raise ValueError(f"Path does not exist: {resolved}")


def _resolve_marketplace_source(source: dict[str, Any], cwd: Path) -> dict[str, Any]:
    resolved = dict(source)
    source_type = str(resolved.get("source") or "")
    if source_type in {"file", "directory"}:
        raw_path = str(resolved.get("path") or "")
        path = Path(raw_path)
        if raw_path.startswith("~"):
            path = Path.home() / raw_path[1:]
        if not path.is_absolute():
            path = (cwd / path).resolve()
        else:
            path = path.resolve()
        resolved["path"] = str(path)
    return resolved


def _materialize_marketplace_source(
    source: dict[str, Any],
    config_home: Path,
) -> tuple[str, Path]:
    source_type = str(source.get("source") or "")
    if source_type == "directory":
        directory = Path(str(source["path"])).resolve()
        manifest_path = _find_marketplace_manifest(directory)
        result = validate_marketplace_manifest(manifest_path)
        _raise_for_validation_failure(result)
        name = _load_marketplace_name(manifest_path)
        return name, directory
    if source_type == "file":
        file_path = Path(str(source["path"])).resolve()
        result = validate_marketplace_manifest(file_path)
        _raise_for_validation_failure(result)
        name = _load_marketplace_name(file_path)
        return name, file_path
    if source_type == "url":
        cache_dir = get_marketplaces_cache_dir(config_home)
        cache_dir.mkdir(parents=True, exist_ok=True)
        temp_path = cache_dir / f".tmp-{uuid4().hex}.json"
        _download_marketplace_json(str(source["url"]), temp_path)
        try:
            result = validate_marketplace_manifest(temp_path)
            _raise_for_validation_failure(result)
            name = _load_marketplace_name(temp_path)
            final_path = cache_dir / f"{name}.json"
            final_path.unlink(missing_ok=True)
            temp_path.replace(final_path)
            return name, final_path
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
    if source_type in {"git", "github"}:
        cache_dir = get_marketplaces_cache_dir(config_home)
        cache_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = cache_dir / f".tmp-{uuid4().hex}"
        _clone_marketplace_repo(source, temp_dir)
        try:
            manifest_path = _find_marketplace_manifest(temp_dir)
            result = validate_marketplace_manifest(manifest_path)
            _raise_for_validation_failure(result)
            name = _load_marketplace_name(manifest_path)
            final_dir = cache_dir / name
            if final_dir.exists():
                shutil.rmtree(final_dir)
            temp_dir.replace(final_dir)
            return name, final_dir
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    raise ValueError(f"Unsupported marketplace source: {source_type}")


def _refresh_marketplace_source(
    source: dict[str, Any],
    install_location: Path,
    config_home: Path,
) -> tuple[str, Path]:
    source_type = str(source.get("source") or "")
    if source_type in {"directory", "file", "url"}:
        return _materialize_marketplace_source(source, config_home)
    if source_type not in {"git", "github"}:
        raise ValueError(f"Unsupported marketplace source: {source_type}")

    if not install_location.exists():
        return _materialize_marketplace_source(source, config_home)

    git_target = install_location.resolve()
    subprocess.run(
        ["git", "-C", str(git_target), "pull", "origin", "HEAD"],
        capture_output=True,
        check=False,
        encoding="utf-8",
    )
    manifest_path = _find_marketplace_manifest(git_target)
    result = validate_marketplace_manifest(manifest_path)
    _raise_for_validation_failure(result)
    name = _load_marketplace_name(manifest_path)
    return name, git_target


def _cleanup_old_marketplace_cache(
    previous_entry: dict[str, Any],
    new_install_location: Path,
    config_home: Path,
) -> None:
    old_install = previous_entry.get("installLocation")
    if not isinstance(old_install, str):
        return
    old_path = Path(old_install)
    if not old_path.exists():
        return
    cache_dir = get_marketplaces_cache_dir(config_home).resolve()
    resolved_old = old_path.resolve()
    resolved_new = new_install_location.resolve()
    if resolved_old == resolved_new:
        return
    if resolved_old == cache_dir or str(resolved_old).startswith(str(cache_dir) + os.sep):
        if resolved_old.is_dir():
            shutil.rmtree(resolved_old, ignore_errors=True)
        else:
            resolved_old.unlink(missing_ok=True)


def _find_marketplace_manifest(root: Path) -> Path:
    candidates = [
        root / ".claude-plugin" / "marketplace.json",
        root / "marketplace.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _load_marketplace_name(manifest_path: Path) -> str:
    parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid marketplace manifest: {manifest_path}")
    name = parsed.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Marketplace manifest has no valid name: {manifest_path}")
    return name.strip()


def _download_marketplace_json(url: str, destination: Path) -> None:
    try:
        with urlopen(url) as response:
            payload = response.read()
    except HTTPError as exc:
        raise ValueError(f"Failed to download marketplace: HTTP {exc.code}") from exc
    except URLError as exc:
        raise ValueError(f"Failed to download marketplace: {exc.reason}") from exc
    destination.write_bytes(payload)


def _clone_marketplace_repo(source: dict[str, Any], destination: Path) -> None:
    repo_url = _git_clone_url(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    clone = subprocess.run(
        ["git", "clone", repo_url, str(destination)],
        capture_output=True,
        check=False,
        encoding="utf-8",
    )
    if clone.returncode != 0:
        stderr = clone.stderr.strip() or clone.stdout.strip() or "git clone failed"
        raise ValueError(stderr)

    ref = source.get("ref")
    if isinstance(ref, str) and ref.strip():
        checkout = subprocess.run(
            ["git", "-C", str(destination), "checkout", ref],
            capture_output=True,
            check=False,
            encoding="utf-8",
        )
        if checkout.returncode != 0:
            stderr = checkout.stderr.strip() or checkout.stdout.strip() or "git checkout failed"
            raise ValueError(stderr)


def _git_clone_url(source: dict[str, Any]) -> str:
    source_type = str(source.get("source") or "")
    if source_type == "git":
        return str(source["url"])
    if source_type == "github":
        return f"https://github.com/{source['repo']}.git"
    raise ValueError(f"Unsupported git marketplace source: {source_type}")


def _raise_for_validation_failure(result: ValidationResult) -> None:
    if result.success:
        return
    if result.errors:
        first = result.errors[0]
        raise ValueError(f"{first.path}: {first.message}")
    raise ValueError("Validation failed")


def _format_marketplace_source(source: dict[str, Any]) -> str:
    source_type = str(source.get("source") or "")
    if source_type == "github":
        return f"GitHub ({source.get('repo', '')})"
    if source_type == "git":
        return f"Git ({source.get('url', '')})"
    if source_type == "url":
        return f"URL ({source.get('url', '')})"
    if source_type == "directory":
        return f"Directory ({source.get('path', '')})"
    if source_type == "file":
        return f"File ({source.get('path', '')})"
    return source_type or "Unknown"


def _now_iso8601() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_plugin_record(
    name: str,
    records: list[PluginRecord],
) -> tuple[PluginRecord | None, str | None]:
    matches = [record for record in records if record.name == name]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return (
            None,
            f'Found {len(matches)} installed plugins named "{name}". Please remove or rename one of them first.',
        )
    return None, f'Plugin "{name}" was not found.'


def set_plugin_disabled(record: PluginRecord, disabled: bool) -> None:
    manifest_path = record.path / "plugin.json"
    manifest = _read_manifest(manifest_path)
    manifest["name"] = str(manifest.get("name") or record.name)
    manifest["disabled"] = disabled
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def uninstall_plugin(record: PluginRecord) -> None:
    shutil.rmtree(record.path)


def validate_manifest(target: str, cwd: Path) -> ValidationResult:
    absolute_path = Path(target)
    if not absolute_path.is_absolute():
        absolute_path = (cwd / absolute_path).resolve()
    else:
        absolute_path = absolute_path.resolve()

    if absolute_path.is_dir():
        marketplace_path = absolute_path / ".claude-plugin" / "marketplace.json"
        marketplace_result = validate_marketplace_manifest(marketplace_path)
        if not _is_not_found(marketplace_result):
            return marketplace_result

        plugin_path = absolute_path / ".claude-plugin" / "plugin.json"
        plugin_result = validate_plugin_manifest(plugin_path)
        if not _is_not_found(plugin_result):
            return plugin_result

        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="directory",
                    message=(
                        "No manifest found in directory. Expected "
                        ".claude-plugin/marketplace.json or .claude-plugin/plugin.json"
                    ),
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="plugin",
        )

    manifest_type = _detect_manifest_type(absolute_path)
    if manifest_type == "plugin":
        return validate_plugin_manifest(absolute_path)
    if manifest_type == "marketplace":
        return validate_marketplace_manifest(absolute_path)

    try:
        parsed = json.loads(absolute_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="file",
                    message=f"File not found: {absolute_path}",
                    code="ENOENT",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="plugin",
        )
    except json.JSONDecodeError as exc:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="json",
                    message=f"Invalid JSON syntax: {exc.msg}",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="plugin",
        )

    if isinstance(parsed, dict) and isinstance(parsed.get("plugins"), list):
        return validate_marketplace_manifest(absolute_path)
    return validate_plugin_manifest(absolute_path)


def validate_plugin_manifest(file_path: Path) -> ValidationResult:
    absolute_path = file_path.resolve()
    errors: list[ValidationMessage] = []
    warnings: list[ValidationMessage] = []

    try:
        parsed = json.loads(absolute_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="file",
                    message=f"File not found: {absolute_path}",
                    code="ENOENT",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="plugin",
        )
    except PermissionError as exc:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="file",
                    message=f"Failed to read file: {exc}",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="plugin",
        )
    except IsADirectoryError:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="file",
                    message=f"Path is not a file: {absolute_path}",
                    code="EISDIR",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="plugin",
        )
    except json.JSONDecodeError as exc:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="json",
                    message=f"Invalid JSON syntax: {exc.msg}",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="plugin",
        )

    if not isinstance(parsed, dict):
        errors.append(
            ValidationMessage(
                path="root",
                message="Plugin manifest must be a JSON object.",
            )
        )
    else:
        name = parsed.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(
                ValidationMessage(
                    path="name",
                    message="Plugin name cannot be empty",
                )
            )
        elif " " in name:
            errors.append(
                ValidationMessage(
                    path="name",
                    message='Plugin name cannot contain spaces. Use kebab-case (e.g., "my-plugin")',
                )
            )

        _validate_string_field(parsed, "version", warnings, optional=True)
        _validate_string_field(parsed, "description", warnings, optional=True)
        _validate_author_field(parsed.get("author"), warnings)
        _validate_bool_field(parsed, "disabled", errors)
        _validate_string_field(parsed, "commands_dir", errors)
        _validate_string_field(parsed, "skills_dir", errors)
        _validate_string_list_field(parsed, "commands_paths", errors)
        _validate_string_list_field(parsed, "skills_paths", errors)
        _check_path_traversal(parsed.get("commands_dir"), "commands_dir", errors)
        _check_path_traversal(parsed.get("skills_dir"), "skills_dir", errors)
        _check_path_traversal_in_list(parsed.get("commands_paths"), "commands_paths", errors)
        _check_path_traversal_in_list(parsed.get("skills_paths"), "skills_paths", errors)

        if "version" not in parsed:
            warnings.append(
                ValidationMessage(
                    path="version",
                    message='No version specified. Consider adding a version following semver (e.g., "1.0.0")',
                )
            )
        if "description" not in parsed:
            warnings.append(
                ValidationMessage(
                    path="description",
                    message="No description provided. Adding a description helps users understand what your plugin does",
                )
            )
        if "author" not in parsed:
            warnings.append(
                ValidationMessage(
                    path="author",
                    message="No author information provided. Consider adding author details for plugin attribution",
                )
            )

    return ValidationResult(
        success=not errors,
        errors=errors,
        warnings=warnings,
        file_path=str(absolute_path),
        file_type="plugin",
    )


def validate_marketplace_manifest(file_path: Path) -> ValidationResult:
    absolute_path = file_path.resolve()
    errors: list[ValidationMessage] = []
    warnings: list[ValidationMessage] = []

    try:
        parsed = json.loads(absolute_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="file",
                    message=f"File not found: {absolute_path}",
                    code="ENOENT",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="marketplace",
        )
    except PermissionError as exc:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="file",
                    message=f"Failed to read file: {exc}",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="marketplace",
        )
    except IsADirectoryError:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="file",
                    message=f"Path is not a file: {absolute_path}",
                    code="EISDIR",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="marketplace",
        )
    except json.JSONDecodeError as exc:
        return ValidationResult(
            success=False,
            errors=[
                ValidationMessage(
                    path="json",
                    message=f"Invalid JSON syntax: {exc.msg}",
                )
            ],
            warnings=[],
            file_path=str(absolute_path),
            file_type="marketplace",
        )

    if not isinstance(parsed, dict):
        errors.append(
            ValidationMessage(
                path="root",
                message="Marketplace manifest must be a JSON object.",
            )
        )
    else:
        name = parsed.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(
                ValidationMessage(
                    path="name",
                    message="Marketplace must have a name",
                )
            )
        plugins = parsed.get("plugins")
        if not isinstance(plugins, list):
            errors.append(
                ValidationMessage(
                    path="plugins",
                    message="Marketplace plugins must be an array.",
                )
            )
        elif not plugins:
            warnings.append(
                ValidationMessage(
                    path="plugins",
                    message="Marketplace has no plugins defined",
                )
            )
        else:
            seen_names: set[str] = set()
            for index, plugin in enumerate(plugins):
                if not isinstance(plugin, dict):
                    errors.append(
                        ValidationMessage(
                            path=f"plugins[{index}]",
                            message="Plugin entry must be a JSON object.",
                        )
                    )
                    continue
                plugin_name = plugin.get("name")
                if not isinstance(plugin_name, str) or not plugin_name.strip():
                    errors.append(
                        ValidationMessage(
                            path=f"plugins[{index}].name",
                            message="Plugin name cannot be empty",
                        )
                    )
                elif plugin_name in seen_names:
                    errors.append(
                        ValidationMessage(
                            path=f"plugins[{index}].name",
                            message=f'Duplicate plugin name "{plugin_name}" found in marketplace',
                        )
                    )
                else:
                    seen_names.add(plugin_name)

                if "source" not in plugin:
                    errors.append(
                        ValidationMessage(
                            path=f"plugins[{index}].source",
                            message="Where to fetch the plugin from is required",
                        )
                    )
                elif isinstance(plugin["source"], str):
                    _check_path_traversal(
                        plugin["source"],
                        f"plugins[{index}].source",
                        errors,
                    )

        metadata = parsed.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(
                ValidationMessage(
                    path="metadata",
                    message="Marketplace metadata must be a JSON object.",
                )
            )
        elif isinstance(metadata, dict):
            description = metadata.get("description")
            if description is not None and not isinstance(description, str):
                errors.append(
                    ValidationMessage(
                        path="metadata.description",
                        message="Marketplace description must be a string.",
                    )
                )
            if "description" not in metadata:
                warnings.append(
                    ValidationMessage(
                        path="metadata.description",
                        message="No marketplace description provided. Adding a description helps users understand what this marketplace offers",
                    )
                )

    return ValidationResult(
        success=not errors,
        errors=errors,
        warnings=warnings,
        file_path=str(absolute_path),
        file_type="marketplace",
    )


def format_validation_result(result: ValidationResult) -> str:
    output = f"Validating {result.file_type} manifest: {result.file_path}\n\n"
    if result.errors:
        output += f"X Found {len(result.errors)} {_plural(len(result.errors), 'error')}:\n\n"
        for error in result.errors:
            output += f"  - {error.path}: {error.message}\n"
        output += "\n"
    if result.warnings:
        output += f"! Found {len(result.warnings)} {_plural(len(result.warnings), 'warning')}:\n\n"
        for warning in result.warnings:
            output += f"  - {warning.path}: {warning.message}\n"
        output += "\n"
    if result.success:
        if result.warnings:
            output += "OK Validation passed with warnings\n"
        else:
            output += "OK Validation passed\n"
    else:
        output += "X Validation failed\n"
    return output


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return dict(parsed)


def _detect_manifest_type(path: Path) -> str:
    name = path.name
    if name == "plugin.json":
        return "plugin"
    if name == "marketplace.json":
        return "marketplace"
    if path.parent.name == ".claude-plugin":
        return "plugin"
    return "unknown"


def _is_not_found(result: ValidationResult) -> bool:
    return len(result.errors) == 1 and result.errors[0].code == "ENOENT"


def _validate_bool_field(
    payload: dict[str, Any],
    field: str,
    errors: list[ValidationMessage],
) -> None:
    if field in payload and not isinstance(payload[field], bool):
        errors.append(
            ValidationMessage(
                path=field,
                message=f"{field} must be a boolean.",
            )
        )


def _validate_string_field(
    payload: dict[str, Any],
    field: str,
    messages: list[ValidationMessage],
    optional: bool = False,
) -> None:
    if field not in payload:
        return
    if payload[field] is None and optional:
        return
    if not isinstance(payload[field], str):
        messages.append(
            ValidationMessage(
                path=field,
                message=f"{field} must be a string.",
            )
        )


def _validate_string_list_field(
    payload: dict[str, Any],
    field: str,
    errors: list[ValidationMessage],
) -> None:
    if field not in payload:
        return
    value = payload[field]
    if isinstance(value, str):
        return
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(
            ValidationMessage(
                path=field,
                message=f"{field} must be a string or array of strings.",
            )
        )


def _validate_author_field(
    value: object,
    warnings: list[ValidationMessage],
) -> None:
    if value is None:
        return
    if isinstance(value, str):
        return
    if isinstance(value, dict):
        name = value.get("name")
        if name is not None and not isinstance(name, str):
            warnings.append(
                ValidationMessage(
                    path="author.name",
                    message="Author name should be a string.",
                )
            )
        return
    warnings.append(
        ValidationMessage(
            path="author",
            message="Author should be a string or object.",
        )
    )


def _check_path_traversal(
    value: object,
    field: str,
    errors: list[ValidationMessage],
) -> None:
    if isinstance(value, str) and ".." in value:
        errors.append(
            ValidationMessage(
                path=field,
                message=f'Path contains "..": {value}',
            )
        )


def _check_path_traversal_in_list(
    value: object,
    field: str,
    errors: list[ValidationMessage],
) -> None:
    if isinstance(value, str):
        _check_path_traversal(value, field, errors)
        return
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        _check_path_traversal(item, f"{field}[{index}]", errors)


def _plural(count: int, singular: str) -> str:
    if count == 1:
        return singular
    return f"{singular}s"
