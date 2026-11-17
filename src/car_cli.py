"""CAR public map CLI. Run: python -m src.car_cli"""
import argparse
from datetime import datetime
from pathlib import Path
import sys

from .coordinates import parse_coordinate
from .browser_session import launch_session

ROOT = Path(__file__).resolve().parent.parent


def ask_coordinate(axis: str, supplied: str | None) -> float:
    while True:
        value = supplied if supplied is not None else input(f"{axis.title()}: ")
        try:
            return parse_coordinate(value, axis)
        except ValueError as exc:
            if supplied is not None:
                raise
            print(f"Invalid value: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Open a CAR property's details from coordinates.")
    parser.add_argument("--lat", help="Latitude; negative for south")
    parser.add_argument("--lon", help="Longitude; negative for west")
    parser.add_argument("--timeout", type=int, default=90, help="Timeout per step in seconds")
    parser.add_argument("--record", action="store_true", help="Record the browser session to WebM")
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    print("CAR public map - enter decimal degrees or DMS.\nSouth and west are negative.")
    try:
        lat = ask_coordinate("latitude", args.lat)
        lon = ask_coordinate("longitude", args.lon)
    except ValueError as exc:
        parser.error(str(exc))
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
    from .portal import open_property, PortalError

    run_dir = ROOT / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        options = {"viewport": {"width": 1280, "height": 900}, "locale": "pt-BR"}
        if args.record:
            options["record_video_dir"] = str(run_dir)
            options["record_video_size"] = {"width": 1280, "height": 900}
        try:
            context = launch_session(playwright, **options)
        except PlaywrightError as exc:
            print(f"Could not start Google Chrome: {exc}\nCheck Chrome is installed and close any other app session.")
            return 1
        browser = context.browser
        page = context.pages[0] if context.pages else context.new_page()
        result = 0
        try:
            code = open_property(page, lat, lon, args.timeout)
            page.screenshot(path=str(run_dir / "property-details.png"), full_page=True)
            print(f"\nProperty details opened. CAR: {code}")
            print("Automation stopped. Continue manually in the browser.")
        except (PortalError, PlaywrightError, ValueError) as exc:
            result = 1
            print(f"\nCould not complete automatically: {exc}", file=sys.stderr)
            if not page.is_closed():
                try:
                    page.screenshot(path=str(run_dir / "error.png"), full_page=True)
                except PlaywrightError:
                    pass
            print("The browser is available for manual inspection. No nearby property was substituted.")
        try:
            input("\nPress Enter here ONLY when finished to close the browser... ")
        except EOFError:
            # A noninteractive launch must not immediately take away the browser.
            while browser.is_connected() and context.pages:
                try:
                    context.pages[0].wait_for_timeout(500)
                except PlaywrightError:
                    break
        finally:
            context.close()
        print(f"Session files: {run_dir}")
        return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)
