"""One isolated browser session. JSON stdout is consumed by the desktop UI."""
import argparse
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from .portal import open_property
from .browser_session import launch_session
from .diagnostics import SessionDiagnostics


def emit(event: str, **values) -> None:
    print(json.dumps({"event": event, **values}), flush=True)


def set_window(page, visible: bool) -> None:
    session = page.context.new_cdp_session(page)
    try:
        window_id = session.send("Browser.getWindowForTarget")["windowId"]
        session.send("Browser.setWindowBounds", {
            "windowId": window_id,
            "bounds": {"windowState": "normal" if visible else "minimized"},
        })
        if visible:
            session.send("Browser.setWindowBounds", {
                "windowId": window_id,
                "bounds": {"left": 70, "top": 50, "width": 1280, "height": 900},
            })
            page.bring_to_front()
    finally:
        session.detach()


def run(latitude: float, longitude: float) -> int:
    ready = False
    diagnostics = SessionDiagnostics(Path(__file__).resolve().parent.parent / "logs")
    with sync_playwright() as playwright:
        browser = None
        context = None
        try:
            emit("progress", stage="browser", message="Starting your browser session...")
            context = launch_session(playwright, minimized=True, viewport=None, locale="pt-BR")
            diagnostics.attach(context)
            browser = context.browser
            page = context.pages[0] if context.pages else context.new_page()
            set_window(page, False)
            selected = []
            code = open_property(page, latitude, longitude, on_selected=selected.append,
                                 progress=lambda stage, message: emit("progress", stage=stage, message=message))
            set_window(page, True)
            ready = True
            diagnostics.write("manual_handoff")
            emit("ready", registration=code, id_origin=selected[0].id_origin)
            # Pump Playwright events; sleeping the Python thread would miss close events.
            while browser.is_connected() and context.pages:
                context.pages[0].wait_for_timeout(250)
            emit("closed")
            return 0
        except Exception as exc:
            if ready and browser and (not browser.is_connected() or not browser.contexts
                                      or not any(c.pages for c in browser.contexts)):
                emit("closed")
                return 0
            emit("error", message=str(exc))
            return 1
        finally:
            if context and browser and browser.is_connected():
                context.close()
            diagnostics.write("session_ended")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    args = parser.parse_args()
    sys.exit(run(args.lat, args.lon))
