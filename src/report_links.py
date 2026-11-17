"""Open the public statement route in ordinary Chrome, outside automation."""
import os
from pathlib import Path
import shutil
import subprocess

from .car_api import normalize_registration


def statement_url(registration: str) -> str:
    return "https://www.car.gov.br/#/consultar/" + normalize_registration(registration)


def open_statement(registration: str) -> None:
    url = statement_url(registration)
    candidates = [shutil.which("chrome")]
    for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        folder = os.environ.get(variable)
        if folder:
            candidates.append(str(Path(folder) / "Google/Chrome/Application/chrome.exe"))
    chrome = next((path for path in candidates if path and Path(path).is_file()), None)
    if not chrome:
        raise OSError("Google Chrome was not found. Install Chrome and try again.")
    # No automation flags or profile override: Chrome owns this independent window.
    subprocess.Popen([chrome, "--new-window", url])
