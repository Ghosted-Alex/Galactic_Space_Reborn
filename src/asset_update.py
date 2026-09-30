"""Asset Update and Sync Module"""

import json
import os
import pathlib
import zipfile
import urllib.request
from . import logger

is_beta = False
test = False

REMOTE_JSON_URL = "https://raw.githubusercontent.com/Ghosted-Alex/Galactic_Space_Reborn/main/assets/assets.json"
REMOTE_ZIP_URL = "https://gitlab.com/Ghosted-Alex/Galactic_Space_Reborn/raw/main/assets/assets.zip"

TEST_REMOTE_URL = "http://0.0.0.0:8000/assets.json"

