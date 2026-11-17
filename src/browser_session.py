"""Application-owned Chrome profile; never reuse the user's personal profile."""
from pathlib import Path
from playwright.sync_api import Playwright, BrowserContext

PROFILE = Path(__file__).resolve().parent.parent / "config" / "chrome-profile"


def launch_session(playwright: Playwright, *, minimized: bool = False,
                   profile: Path = PROFILE, **options) -> BrowserContext:
    profile.mkdir(parents=True, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile), channel="chrome", headless=False,
        args=["--start-minimized"] if minimized else [],
        **options,
    )
