"""Asset Update and Sync Module"""

import json
import os
import random
import pathlib
import shutil
import zipfile
import urllib.request
import time
from . import logger
from .utilities import ProgressBar

beta = True

REMOTE_JSON_URL = "https://gitlab.com/ghostedalex/project-data-server/raw/main/galactic_space_reborn/assets.json"
REMOTE_ZIP_URL = "https://gitlab.com/ghostedalex/project-data-server/raw/main/galactic_space_reborn/assets.zip"

DEBUG_REMOTE_URL = "http://0.0.0.0:8000/assets.json"
DEBUG_ZIP_URL = "http://0.0.0.0:8000/assets.zip"

def sync_remote_assets(local_assets_dir: pathlib.Path, debug: bool = False):
    yield 0, "Preparing..."
    local_assets_dir.mkdir(parents=True, exist_ok=True)
    local_manifest = local_assets_dir / "assets.json"
    local_version = [0, 0, 0]

    target_json_url = DEBUG_REMOTE_URL if debug else REMOTE_JSON_URL
    target_zip_url = DEBUG_ZIP_URL if debug else REMOTE_ZIP_URL

    time.sleep(0.5)

    yield 20, "Reading local manifest..."
    if local_manifest.exists():
        try:
            with open(local_manifest, "r") as f:
                data = json.load(f)
                local_version = data.get("asset_version", [0, 0, 0])
                time.sleep(0.75)
        except Exception as e:
            logger.engine_log.warning(f"Could not parse local asset_version: {e}")
            time.sleep(0.1)

    yield 40, "Checking for remote updates..."
    remote_version = None
    try:
        req = urllib.request.Request(target_json_url, headers={'User-Agent': 'GSEngine-Updater'})
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status == 200:
                remote_data = json.loads(response.read().decode('utf-8'))
                remote_version = remote_data.get("asset_version", [0, 0, 0])
                time.sleep(0.5)
    except Exception as e:
        time.sleep(1.5)
        yield 100, "Offline mode: using local assets"
        return

    if remote_version and remote_version > local_version:
        yield 60, f"New assets found ({remote_version}). Downloading..."
        temp_zip = local_assets_dir / "temp_assets.zip"

        time.sleep(1.25)

        try:
            urllib.request.urlretrieve(target_zip_url, temp_zip)
            yield 80, "Extracting asset archive..."

            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                namelist = zip_ref.namelist()
                first_part = namelist[0].split('/')[0] if namelist else ""
                has_wrapper = all(name.startswith(first_part + '/') for name in namelist if name)

                for member in zip_ref.infolist():
                    parts = pathlib.Path(member.filename).parts
                    rel_parts = parts[1:] if (has_wrapper and len(parts) > 1) else parts
                    if not rel_parts:
                        continue
                    target_path = local_assets_dir.joinpath(*rel_parts)
                    if member.is_dir():
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            shutil.copyfileobj(source, target)

            time.sleep(1.3)

            if temp_zip.exists():
                os.remove(temp_zip)
            yield 100, "Assets updated successfully!"
        except Exception as e:
            if temp_zip.exists():
                os.remove(temp_zip)

            time.sleep(3.5)
            yield 100, "Update failed: fallback to local assets"
    else:
        yield 100, "Assets up to date"
class AssetUpdater:
    def __init__(self, assets_dir: pathlib.Path = pathlib.Path("assets"), debug: bool = False):
        self.assets_dir = assets_dir
        self.debug = debug
        self.progress_bar = ProgressBar(length=50)

    def run(self) -> None:
        logger.asset_thread_log.info("Checking for Asset Updates...")
        
        loader = sync_remote_assets(self.assets_dir, debug=self.debug)
        
        try:
            while True:
                pct_val, message = next(loader)
                self.progress_bar.update(pct_val, message)
                time.sleep(0.15)
        except StopIteration:
            readiness = 0
            while readiness < 100:
                readiness += random.randint(1, 10)
                if readiness < 100:
                    self.progress_bar.update(readiness, "Preparing to launch game...")
                    time.sleep(random.random()/8)
                else:
                    self.progress_bar.update(readiness, "Ready! Launching game...")
                    time.sleep(1)

            print()