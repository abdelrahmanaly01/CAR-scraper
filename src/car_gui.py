"""Desktop interface; browser work runs outside Tk's UI thread."""
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog

from .coordinates import parse_coordinate
from .report_links import open_statement
from .downloads import download_zip
from .translations import LANGUAGES, TEXT, error_key

ROOT = Path(__file__).resolve().parent.parent
BG = "#f3f6fa"
INK = "#172c42"
MUTED = "#65758a"
ACCENT = "#16785b"
LINE = "#e2e9ef"
CARD = "#ffffff"
MAX_CONTENT_WIDTH = 960


class CarApp:
    def __init__(self, root: tk.Tk, settings_path: Path | None = None):
        self.root = root
        self.settings_path = settings_path or ROOT / "config" / "preferences.json"
        self.language = "en"
        try:
            saved = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if isinstance(saved, dict) and saved.get("language") in LANGUAGES:
                self.language = saved["language"]
        except (OSError, ValueError):
            pass
        self.translated_widgets = []
        self.status_key = "idle"
        self.error_key = None
        self.current_stage = None
        self.process = None
        self.events = queue.Queue()
        self.busy = False
        self.ready = False
        self.registration = None
        self.id_origin = None
        self.downloading = False
        self.download_events = queue.Queue()
        self.pending_finish = None
        self.cancelled = False
        self.failure = None
        self.session_id = 0
        self.closing = False
        self.candidates = []
        root.title("CAR | Property Finder")
        root.geometry("760x820+80+30")
        root.minsize(420, 300)
        if os.name == "nt":
            root.state("zoomed")
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TEntry", padding=11, font=("Segoe UI", 12),
                        fieldbackground="white", bordercolor=LINE, lightcolor=LINE,
                        darkcolor=LINE)
        style.map("TEntry", bordercolor=[("focus", ACCENT)],
                  lightcolor=[("focus", ACCENT)], darkcolor=[("focus", ACCENT)])
        style.configure("TCombobox", padding=9, font=("Segoe UI", 10),
                        fieldbackground="white", background="white", bordercolor=LINE)
        style.map("TCombobox", fieldbackground=[("readonly", "white")],
                  selectbackground=[("readonly", "white")],
                  selectforeground=[("readonly", INK)])
        style.configure("Primary.TButton", font=("Segoe UI Semibold", 11), padding=13,
                        background=ACCENT, foreground="white", borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#116448"), ("disabled", "#a3b9b2")],
                  foreground=[("disabled", "#f4f7f6")])
        style.configure("Secondary.TButton", font=("Segoe UI Semibold", 9), padding=9,
                        background="#edf2f6", foreground=INK, borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#dce6ed"), ("disabled", "#f1f3f5")])
        style.configure("Green.Horizontal.TProgressbar", background=ACCENT,
                        troughcolor="#e6edf3", borderwidth=0)
        viewport = tk.Frame(root, bg=BG)
        viewport.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(viewport, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(viewport, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        outer = tk.Frame(self.canvas, bg=BG, padx=28, pady=24)
        content = self.canvas.create_window((0, 0), window=outer, anchor="nw")
        outer.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.content_window = content
        self.canvas.bind("<Configure>", self.resize_content)
        root.bind_all("<MouseWheel>", self.scroll_wheel, add="+")
        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x")
        self.language_choice = tk.StringVar(value=LANGUAGES[self.language])
        selector = ttk.Combobox(header, textvariable=self.language_choice,
                               values=list(LANGUAGES.values()), state="readonly", width=20)
        selector.pack(side="right")
        selector.bind("<<ComboboxSelected>>", self.change_language)
        self.localized_label(header, "brand", 10, ACCENT, True).pack(side="left")
        self.localized_label(outer, "title", 27, INK, True).pack(anchor="w", pady=(24, 5))
        self.localized_label(outer, "intro", 11, MUTED).pack(anchor="w", pady=(0, 18))

        card = tk.Frame(outer, bg=CARD, padx=24, pady=20,
                        highlightbackground=LINE, highlightthickness=1)
        card.pack(fill="x", pady=(0, 12))
        self.localized_label(card, "coordinates_heading", 13, INK, True).pack(anchor="w")
        self.localized_label(card, "coordinates_intro", 10, MUTED).pack(anchor="w", pady=(4, 17))
        fields = tk.Frame(card, bg=CARD)
        fields.pack(fill="x")
        fields.columnconfigure((0, 1), weight=1)
        self.latitude = tk.StringVar()
        self.longitude = tk.StringVar()
        self.entries = []
        for column, (title, variable, hint) in enumerate([
            ("latitude", self.latitude, "south"),
            ("longitude", self.longitude, "west"),
        ]):
            frame = tk.Frame(fields, bg=CARD)
            frame.grid(row=0, column=column, sticky="ew", padx=(0, 8) if column == 0 else (8, 0))
            self.localized_label(frame, title, 10, INK, True).pack(anchor="w", pady=(0, 6))
            entry = ttk.Entry(frame, textvariable=variable, width=20)
            entry.pack(fill="x")
            self.entries.append(entry)
            self.localized_label(frame, hint, 9, MUTED).pack(anchor="w", pady=(6, 0))
        actions = tk.Frame(card, bg=CARD)
        actions.pack(fill="x", pady=(17, 0))
        self.example = ttk.Button(actions, text="Use sample coordinates", style="Secondary.TButton", command=self.fill_sample)
        self.example.pack(side="left")
        self.start_button = ttk.Button(actions, text="Find property", style="Primary.TButton", command=self.start)
        self.start_button.pack(side="right")
        self.translated_widgets.extend([(self.example, "sample"), (self.start_button, "find")])
        self.error = self.label(card, "", 9, "#b23d3d")
        self.error.configure(wraplength=700, justify="left")
        self.error.pack(anchor="w", fill="x", pady=(8, 0))

        status_card = tk.Frame(outer, bg=CARD, padx=24, pady=18,
                               highlightbackground=LINE, highlightthickness=1)
        status_card.pack(fill="x", pady=(0, 12))
        status_header = tk.Frame(status_card, bg=CARD)
        status_header.pack(fill="x")
        self.localized_label(status_header, "progress_heading", 11, MUTED, True).pack(side="left")
        self.cancel_button = ttk.Button(status_header, text="Cancel", style="Secondary.TButton", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="right")
        self.status = self.label(status_card, "Ready when you are", 11, INK, True)
        self.status.pack(anchor="w", fill="x", pady=(9, 0))
        self.status.configure(wraplength=700, justify="left")
        self.progress = ttk.Progressbar(status_card, mode="determinate", style="Green.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(14, 0))

        result_card = tk.Frame(outer, bg=CARD, padx=24, pady=18,
                               highlightbackground=LINE, highlightthickness=1)
        result_card.pack(fill="x")
        self.localized_label(result_card, "results_heading", 13, INK, True).pack(anchor="w")
        self.candidate_title = self.label(result_card, "", 9, MUTED)
        self.candidate_title.configure(wraplength=700, justify="left")
        self.candidate_title.pack(anchor="w", fill="x", pady=(5, 10))
        self.candidate_choice = ttk.Combobox(result_card, state="disabled", width=55)
        self.candidate_choice.pack(fill="x")
        self.candidate_choice.bind("<<ComboboxSelected>>", self.select_candidate)
        self.candidate_details = self.label(result_card, "", 10, INK)
        self.candidate_details.configure(wraplength=700, justify="left")
        self.candidate_details.pack(anchor="w", fill="x", pady=(10, 8))
        result_actions = tk.Frame(result_card, bg=CARD)
        result_actions.pack(fill="x", pady=(4, 0))
        self.report_button = ttk.Button(result_actions, style="Secondary.TButton", command=self.open_report, state="disabled")
        self.report_button.pack(side="left")
        self.download_button = ttk.Button(result_actions, style="Secondary.TButton", command=self.save_zip, state="disabled")
        self.download_button.pack(side="right")
        self.translated_widgets.extend([(self.report_button, "statement"),
                                        (self.download_button, "download_zip")])
        self.download_status = self.label(result_card, "", 9, MUTED)
        self.download_status.pack(anchor="w", fill="x", pady=(7, 0))
        root.bind("<Return>", lambda event: self.start() if not self.busy else None)
        root.after(100, self.poll)
        self.entries[0].focus_set()
        self.refresh_language()

    def tr(self, key):
        return TEXT[self.language][key]

    def resize_content(self, event):
        width = min(event.width, MAX_CONTENT_WIDTH)
        self.canvas.itemconfigure(self.content_window, width=width)
        self.canvas.coords(self.content_window, (event.width - width) / 2, 0)
        wraplength = max(240, width - 100)
        for widget in (self.error, self.status, self.candidate_title, self.candidate_details):
            widget.configure(wraplength=wraplength)
        if width < 620:
            self.example.pack_configure(side="top", fill="x", pady=(0, 8))
            self.start_button.pack_configure(side="top", fill="x")
            self.report_button.pack_configure(side="top", fill="x", pady=(0, 7))
            self.download_button.pack_configure(side="top", fill="x", pady=0)
        else:
            self.example.pack_configure(side="left", fill="none", pady=0)
            self.start_button.pack_configure(side="right", fill="none")
            self.report_button.pack_configure(side="left", fill="none", pady=0)
            self.download_button.pack_configure(side="right", fill="none", pady=0)

    def scroll_wheel(self, event):
        # Do not intercept mouse wheel events in combobox popups or other windows.
        if event.widget.winfo_toplevel() == self.root and not isinstance(event.widget, ttk.Combobox):
            self.canvas.yview_scroll(-int(event.delta / 120), 'units')

    def localized_label(self, parent, key, size, color, bold=False):
        widget = self.label(parent, self.tr(key), size, color, bold)
        self.translated_widgets.append((widget, key))
        return widget

    def change_language(self, event=None):
        selected = next((key for key, value in LANGUAGES.items()
                         if value == self.language_choice.get()), "en")
        self.language = selected
        self.refresh_language()
        try:
            self.settings_path.write_text(json.dumps({"language": selected}), encoding="utf-8")
        except OSError:
            self.dialog("window", self.tr("preference_error"))

    def refresh_language(self):
        self.root.title(self.tr("window"))
        for widget, key in self.translated_widgets:
            widget.configure(text=self.tr(key))
        self.status.configure(text=self.tr(self.status_key))
        if self.error_key:
            self.error.configure(text=self.tr(self.error_key))
        self.cancel_button.configure(text=self.tr("end" if self.ready and self.busy else "cancel"))

    def set_status(self, key, color=INK):
        self.status_key = key
        self.status.configure(text=self.tr(key), fg=color)

    def set_error(self, key=None):
        self.error_key = key
        self.error.configure(text=self.tr(key) if key else "")

    def dialog(self, title_key, message, question=False):
        """Own buttons follow the app language instead of the Windows locale."""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.tr(title_key))
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.resizable(False, False)
        result = [False]
        text = self.label(dialog, message, 11, INK)
        text.configure(wraplength=480, justify="left")
        text.pack(padx=24, pady=22)
        buttons = tk.Frame(dialog, bg=BG)
        buttons.pack(fill="x", padx=24, pady=(0, 20))

        def finish(value):
            result[0] = value
            dialog.destroy()

        if question:
            ttk.Button(buttons, text=self.tr("no"), style="Secondary.TButton",
                       command=lambda: finish(False)).pack(side="right", padx=(10, 0))
        primary = ttk.Button(buttons, text=self.tr("yes" if question else "ok"),
                             style="Primary.TButton", command=lambda: finish(True))
        primary.pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", lambda: finish(False))
        dialog.bind("<Escape>", lambda event: finish(False))
        dialog.bind("<Return>", lambda event: finish(True))
        dialog.update_idletasks()
        dialog.geometry(f"+{self.root.winfo_rootx() + 40}+{self.root.winfo_rooty() + 100}")
        dialog.grab_set()
        primary.focus_set()
        self.root.wait_window(dialog)
        return result[0]

    def ask_again(self):
        return self.dialog("finished_title", self.tr("another"), question=True)

    @staticmethod
    def label(parent, text, size, color, bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI Semibold" if bold else "Segoe UI", size))

    def fill_sample(self):
        self.latitude.set("-8.2652558333")
        self.longitude.set("-67.6735275000")

    def open_report(self):
        if not self.registration:
            return
        try:
            open_statement(self.registration)
        except (OSError, ValueError, RuntimeError) as exc:
            self.dialog("window", self.tr("statement_error") + "\n\n" + str(exc))

    def select_candidate(self, event=None):
        index = self.candidate_choice.current()
        if index < 0 or index >= len(self.candidates):
            return
        item = self.candidates[index]
        self.registration, self.id_origin = item['registration'], item['id_origin']
        state = 'inside' if item.get('inside') is True else 'outside' if item.get('inside') is False else 'unknown_boundary'
        distance = item.get('distance_m')
        detail = f"{item.get('city') or ''}, {item.get('state') or ''} | {item.get('area') or '?'} ha\n{self.tr(state)}"
        if distance is not None:
            detail += f" | {self.tr('boundary_distance')}: ~{distance} m"
        self.candidate_details.configure(text=detail)
        self.error.configure(text='CAR: ' + self.registration, fg=ACCENT)
        self.report_button.configure(state='normal')
        self.download_button.configure(state='normal')

    def save_zip(self):
        if self.downloading or not self.registration or not self.id_origin:
            return
        filename = filedialog.asksaveasfilename(parent=self.root, title=self.tr("download_zip"),
                    initialfile=self.registration + '_feicoes.zip', defaultextension='.zip',
                    filetypes=[('ZIP', '*.zip')])
        if not filename:
            return
        self.downloading = True
        self.download_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.download_status.configure(text=self.tr("downloading"))
        origin = self.id_origin

        def work():
            try:
                path = download_zip(origin, filename,
                    lambda received, total: self.download_events.put(('progress', (received, total))))
                self.download_events.put(('done', str(path)))
            except Exception as exc:
                self.download_events.put(('error', str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def poll_download(self):
        while not self.download_events.empty():
            kind, value = self.download_events.get_nowait()
            if kind == 'progress':
                received, total = value
                amount = f'{received / total:.0%}' if total else f'{received // 1024} KB'
                self.download_status.configure(text=self.tr('downloading') + ' ' + amount)
            else:
                self.downloading = False
                key = 'download_saved' if kind == 'done' else 'download_failed'
                self.download_status.configure(text=self.tr(key))
                self.download_button.configure(state='normal' if self.id_origin else 'disabled')
                if not self.busy:
                    self.start_button.configure(state='normal')
                self.dialog('download_zip', self.tr(key) + '\n\n' + value)
                if self.pending_finish is not None:
                    code, self.pending_finish = self.pending_finish, None
                    self.finished(code)
                    return

    def set_inputs(self, enabled):
        state = "normal" if enabled else "disabled"
        for control in [*self.entries, self.example, self.start_button]:
            control.configure(state=state)

    def start(self):
        if self.busy or self.downloading:
            return
        try:
            lat = parse_coordinate(self.latitude.get(), "latitude")
            lon = parse_coordinate(self.longitude.get(), "longitude")
        except ValueError:
            self.set_error("invalid")
            return
        self.set_error()
        self.registration = None
        self.id_origin = None
        self.candidates = []
        self.candidate_choice.configure(values=[], state='disabled')
        self.candidate_choice.set('')
        self.candidate_details.configure(text='')
        self.candidate_title.configure(text='')
        self.download_button.configure(state='disabled')
        self.download_status.configure(text='')
        self.report_button.configure(state="disabled")
        self.busy, self.ready, self.cancelled = True, False, False
        self.failure = None
        self.session_id += 1
        self.set_inputs(False)
        self.cancel_button.configure(state="normal", text=self.tr("cancel"))
        self.set_status("checking_start")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        # pythonw keeps the GUI console-free; the worker needs stdout for JSON.
        interpreter = Path(sys.executable).with_name("python.exe") if os.name == "nt" else Path(sys.executable)
        try:
            self.process = subprocess.Popen(
                [str(interpreter), "-u", "-m", "src.candidate_worker",
                 f"--lat={lat}", f"--lon={lon}"],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except OSError as exc:
            self.failure = str(exc)
            self.finished(1)
            return
        threading.Thread(target=self.read_events, args=(self.process, self.session_id), daemon=True).start()

    def read_events(self, process, session_id):
        tail = []
        for line in process.stdout:
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or "event" not in event:
                    raise ValueError()
            except (ValueError, TypeError):
                tail.append(line.strip())
                tail = tail[-8:]
                continue
            self.events.put((session_id, event))
        self.events.put((session_id, {"event": "finished", "code": process.wait(), "tail": "\n".join(tail)}))

    def update_stage(self, stage, message):
        self.current_stage = stage
        self.set_status("ready" if stage == "done" else "progress_" + stage)

    def poll(self):
        if self.closing:
            return
        self.poll_download()
        if self.closing:
            return
        while not self.events.empty():
            session_id, event = self.events.get_nowait()
            if session_id != self.session_id:
                continue
            kind = event["event"]
            if kind == 'candidate_progress' and not self.cancelled:
                self.status.configure(text=self.tr('checking_candidates').format(current=event['current'], total=event['total']))
            elif kind == 'candidates' and not self.cancelled:
                self.candidates = event['candidates']
                self.search_failures = event['failures']
                if not self.candidates:
                    self.failure = '; '.join(self.search_failures) or 'No CAR property was returned for these coordinates.'
            elif kind == "progress" and not self.cancelled:
                self.update_stage(event["stage"], event["message"])
            elif kind == "ready" and not self.cancelled:
                self.ready = True
                self.registration = event["registration"]
                self.id_origin = event.get("id_origin")
                self.download_button.configure(state='normal' if self.id_origin else 'disabled')
                self.report_button.configure(state="normal")
                self.progress.stop()
                self.progress.configure(mode="determinate", value=100)
                self.update_stage("done", "Property ready — continue in the browser")
                self.error_key = None
                self.error.configure(text=f"CAR: {event['registration']}", fg=ACCENT)
                self.cancel_button.configure(text=self.tr("end"))
            elif kind == "error":
                self.failure = event["message"]
            elif kind == "finished":
                if event["code"] and not self.failure and not self.cancelled:
                    self.failure = event.get("tail") or self.tr("unexpected")
                self.finished(event["code"])
                if self.closing:
                    return
        self.root.after(100, self.poll)

    def finished(self, code):
        if self.downloading:
            self.pending_finish = code
            return
        if self.candidates and not self.cancelled and not self.failure:
            self.busy = False
            self.process = None
            self.progress.stop()
            self.progress.configure(mode='determinate', value=100)
            self.set_inputs(True)
            self.cancel_button.configure(state='disabled')
            self.candidate_title.configure(text=self.tr('partial_results') if getattr(self, 'search_failures', []) else self.tr('candidate_notice'))
            self.candidate_choice.configure(values=[x['registration'] for x in self.candidates], state='readonly')
            self.candidate_choice.set('')
            self.set_status('choose_candidate')
            return
        self.registration = None
        self.id_origin = None
        self.download_button.configure(state='disabled')
        self.report_button.configure(state="disabled")
        self.busy = False
        self.process = None
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.set_inputs(True)
        self.cancel_button.configure(state="disabled")
        self.error.configure(fg="#b23d3d")
        if self.cancelled:
            self.set_status("cancelled")
            self.set_error()
        elif self.failure:
            self.set_status("failed", "#b23d3d")
            self.set_error(error_key(self.failure))
            self.dialog("failed_title", self.tr(self.error_key) + "\n\n" +
                        self.tr("technical") + ":\n" + self.failure[:700])
        elif self.ready:
            self.root.deiconify()
            self.root.lift()
            again = self.ask_again()
            if not again:
                self.close()
                return
            self.set_error()
            self.current_stage = None
            self.set_status("again")
            self.entries[0].focus_set()
            self.entries[0].selection_range(0, "end")

    def stop_process(self, process=None):
        process = process or self.process
        if process and process.poll() is None:
            if os.name == "nt":
                # Only this session's process tree, never unrelated Chrome windows.
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            else:
                process.terminate()

    def cancel(self):
        if not self.busy:
            return
        self.cancelled = True
        self.set_status("closing")
        self.cancel_button.configure(state="disabled")
        threading.Thread(target=self.stop_process, args=(self.process,), daemon=True).start()

    def close(self):
        if self.downloading:
            self.dialog('download_zip', self.tr('download_wait'))
            return
        self.closing = True
        try:
            self.stop_process()
        finally:
            self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    CarApp(window)
    window.mainloop()
