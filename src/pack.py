"""Resource Pack Core Module"""

import pathlib
import json
import os
import pygame
import config

from . import logger

def _manifest_details(data: dict) -> tuple[dict, int | None]:
    """Read both the current and legacy resource-pack manifest layouts."""
    if isinstance(data.get("manifest"), dict):
        return data["manifest"], data.get("format_version")
    format_block = data.get("format", {})
    if isinstance(format_block, dict) and isinstance(format_block.get("manifest"), dict):
        return format_block["manifest"], format_block.get("version")
    return {}, None

def discover_packs() -> list[dict]:
    """Return usable packs in the resource_packs directory with display metadata."""
    packs_dir = pathlib.Path(config.RESOURCE_PACKS_DIR)
    if not packs_dir.is_dir():
        return []

    packs = []
    for pack_dir in sorted(packs_dir.iterdir(), key=lambda item: item.name.lower()):
        manifest_path = pack_dir / "manifest.json"
        if not pack_dir.is_dir() or not manifest_path.is_file():
            continue
        try:
            with manifest_path.open("r", encoding="utf-8") as manifest_file:
                data = json.load(manifest_file)
            manifest, format_version = _manifest_details(data)
            required = ("name", "description", "author", "uuid", "version", "min_engine_version")
            if format_version != config.format_ver or any(manifest.get(key) is None for key in required):
                print(f"[Resource Pack Engine] Ignoring invalid pack: {pack_dir.name}")
                continue
            packs.append({
                "id": pack_dir.name,
                "name": str(manifest["name"]),
                "description": str(manifest["description"]),
                "author": str(manifest["author"]),
                "path": pack_dir,
                "icon_path": pack_dir / "pack_icon.png",
            })
        except (OSError, json.JSONDecodeError) as err:
            logger.rp_thread_log.error(f"Unable to load resource pack \"{pack_dir.name}\": {err}")
    return packs

def load_saved_selection() -> str | None:
    """Load a previously selected pack, falling back safely to vanilla."""
    selected = None
    try:
        with pathlib.Path(config.SETTINGS_FILE).open("r", encoding="utf-8") as settings_file:
            selected = json.load(settings_file).get("resource_pack")
    except (OSError, json.JSONDecodeError, AttributeError):
        # Preserve existing players' selected pack while they transition to settings.json.
        try:
            with pathlib.Path(config.RESOURCE_PACK_SELECTION_FILE).open("r", encoding="utf-8") as legacy_file:
                selected = json.load(legacy_file).get("active_pack")
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
    return selected if any(pack["id"] == selected for pack in discover_packs()) else None

def set_active_pack(pack_name: str | None, persist: bool = True) -> bool:
    """Activate a discovered pack (or ``None`` for vanilla) for this process."""
    valid_names = {pack["id"] for pack in discover_packs()}
    if pack_name is not None and pack_name not in valid_names:
        return False

    config.PACKS_ACTIVE = pack_name is not None
    if pack_name is None:
        os.environ.pop("GSR_ACTIVE_PACK", None)
    else:
        os.environ["GSR_ACTIVE_PACK"] = pack_name

    if persist:
        try:
            settings_path = pathlib.Path(config.SETTINGS_FILE)
            settings = {}
            if settings_path.is_file():
                with settings_path.open("r", encoding="utf-8") as settings_file:
                    settings = json.load(settings_file)
            if not isinstance(settings, dict):
                settings = {}
            settings["resource_pack"] = pack_name
            with settings_path.open("w", encoding="utf-8") as settings_file:
                json.dump(settings, settings_file, indent=2)
        except OSError as err:
            logger.rp_thread_log.error(f"Could not save selected pack: {err}")
        except json.JSONDecodeError:
            logger.rp_thread_log.error("[Resource Pack Engine] Could not read settings.json; saving a fresh settings file.")
            with pathlib.Path(config.SETTINGS_FILE).open("w", encoding="utf-8") as settings_file:
                json.dump({"resource_pack": pack_name}, settings_file, indent=2)
    return True

def load_resources():
    """Restore the selected pack and ensure the general settings file exists."""
    selected_pack = load_saved_selection()
    # Persist on startup so a fresh install receives settings.json immediately,
    # and a legacy resource_pack.json selection is migrated automatically.
    set_active_pack(selected_pack, persist=True)

def is_pack_active() -> bool:
    """Returns True if a resource pack is currently loaded and active."""
    return getattr(config, 'PACKS_ACTIVE', False) and bool(os.environ.get("GSR_ACTIVE_PACK"))

def get_active_pack_name() -> str | None:
    """Returns the name of the active resource pack folder, or None if vanilla."""
    if is_pack_active():
        return os.environ.get("GSR_ACTIVE_PACK")
    return None

def get_active_pack_path() -> pathlib.Path | None:
    """Returns the pathlib.Path to the active resource pack directory, or None if vanilla."""
    pack_name = get_active_pack_name()
    if pack_name:
        return pathlib.Path(config.DATA_PATH) / "resource_packs" / pack_name
    return None

def resolve_asset_path(relative_path: str | pathlib.Path) -> pathlib.Path:
    """Resolves an asset file path, checking the active resource pack workspace first,
    then falling back to vanilla assets.
    """
    rel_path = pathlib.Path(relative_path)
    pack_base = get_active_pack_path()
    vanilla_base = pathlib.Path(config.DATA_PATH)

    if pack_base:
        pack_asset = pack_base / "assets" / rel_path
        if pack_asset.is_file():
            return pack_asset

    return vanilla_base / "assets" / rel_path

def get_merged_manifest() -> dict:
    """Loads core Vanilla manifest data, and merges active resource pack asset overrides over it."""
    vanilla_base = pathlib.Path(config.DATA_PATH)
    vanilla_manifest_path = vanilla_base / "manifest.json"

    with open(vanilla_manifest_path, "r") as f:
        vanilla_data = json.load(f)

    v_assets = vanilla_data.get("assets", {})
    texture_manifest = dict(v_assets.get("textures", {}))
    audio_node = v_assets.get("audio", {})
    sound_manifest = dict(audio_node.get("sound", {}))
    music_manifest = dict(audio_node.get("music", {}))

    if is_pack_active():
        pack_manifest_path = get_active_pack_path() / "manifest.json"
        if pack_manifest_path.is_file():
            try:
                with open(pack_manifest_path, "r") as f:
                    pack_data = json.load(f)

                # Dynamic packs do not have the 'assets' block root key per layout design rules
                pack_assets = pack_data.get("assets", {})
                if "textures" in pack_assets:
                    texture_manifest.update(pack_assets["textures"])
                if "audio" in pack_assets:
                    pack_audio = pack_assets["audio"]
                    if "sound" in pack_audio:
                        sound_manifest.update(pack_audio["sound"])
                    if "music" in pack_audio:
                        music_manifest.update(pack_audio["music"])
            except Exception as err:
                logger.rp_thread_log.error(f"Error loading pack asset overrides: {err}")

    return {
        "textures": texture_manifest,
        "sound": sound_manifest,
        "music": music_manifest
    }

def verify_manifest() -> bool:
    """
    Strictly requires the 'format_version' handshake block in the resource pack's manifest.json.
    Modularly validates asset existence on disk.
    """
    if is_pack_active():
        base_path = get_active_pack_path()
        manifest_path = base_path / "manifest.json"
    else:
        base_path = pathlib.Path(config.DATA_PATH) / "assets"

    if is_pack_active():
        if not manifest_path.is_file():
            logger.rp_thread_log.error(f"manifest.json file missing at: {manifest_path}")
            return False

    if is_pack_active():
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as err:
            logger.rp_thread_log.critical(f"JSON Syntax Error in {manifest_path.name}!")
            logger.rp_thread_log.critical(f"Line {err.lineno}, Column {err.colno}: {err.msg}")
            return False

    # Updated flat validation handshake layer checking for format_version directly
    if is_pack_active():
        try:
            manifest_node, version_node = _manifest_details(data)

            required_keys = ["name", "description", "author", "uuid", "version", "min_engine_version"]
            for key in required_keys:
                if manifest_node.get(key) is None:
                    logger.rp_thread_log.error(f"CRITICAL: Required manifest field '{key}' is missing inside the handshake.")
                    return False

            if version_node != config.format_ver:
                logger.rp_thread_log.critical(f"Manifest is on format version {version_node}, the engine currently supports format version {config.format_ver}")
                return False

        except (KeyError, TypeError) as missing_key:
            logger.rp_thread_log.critical(f"Structural block {missing_key} is missing from manifest.json!")
            return False

        logger.rp_thread_log.info(f"Handshake Confirmed: Loading '{manifest_node['name']}'...")

    missing_files_count = 0
    
    if is_pack_active():
        if "assets" in data:
            assets_node = data["assets"]

            def validate_group_paths(asset_group: dict, group_label: str):
                nonlocal missing_files_count
                for target_var, entry in asset_group.items():
                    rel_path = entry["file"] if isinstance(entry, dict) and "file" in entry else entry
                    if isinstance(rel_path, str):
                        full_target_path = base_path / rel_path
                        if not full_target_path.is_file():
                            logger.rp_thread_log.error(f"Missing {group_label} asset file: '{rel_path}' (Variable: {target_var})")
                            missing_files_count += 1

            if "textures" in assets_node:
                validate_group_paths(assets_node["textures"], "Texture")
            if "audio" in assets_node:
                audio_node = assets_node["audio"]
                if "sound" in audio_node:
                    validate_group_paths(audio_node["sound"], "Sound")
                if "music" in audio_node:
                    validate_group_paths(audio_node["music"], "Music")

    if missing_files_count > 0:
        logger.rp_thread_log.error(f"Validation FAILED. {missing_files_count} declared file(s) are missing from disk layout.")
        return False

    logger.rp_thread_log.info("Success! Resource pack manifest validation completed with zero errors.")
    return True
