# Browser comparison, trial 2 — 2026-11-16

Trial 1 (Chrome with temporary context) did not fix the CAPTCHA loop in the
user's manual test. Trial 2 changes only session persistence: both entry points
use installed Chrome with an app-owned profile at config/chrome-profile/.
No personal browser profile, CAPTCHA solving, or browser fingerprint masking is
used. The 20 existing offline tests pass. Manual CAPTCHA outcome is pending;
these tests do not validate acceptance by reCAPTCHA.

---

# Browser comparison, trial 1 — 2026-11-16

GUI and CLI now launch installed Google Chrome using channel="chrome".
Temporary context, locale, window behavior, property lookup and handoff remain
unchanged. No persistent profile or CAPTCHA automation was added.
Google Chrome is present on the development PC; all 20 offline tests pass.
Manual CAPTCHA outcome is pending the user's test and is not validated by
these offline tests. Test the same property and download action as before.

---

# API-first search — 2026-11-16

Current flow: exact coordinate API lookup → website registration search →
verify identifier response → verify visible details → manual browser handoff.
The legacy map adapter is not imported or executed.

Validation:
- 20 offline tests pass, including exact coordinate forwarding, invalid/empty
  service responses, and rejection of mismatched API or visible registrations.
- Live browser test: (-23.266165, -53.290072) opened
  PR-4107256-605F909883AA43049A3F13A649F9C99A.
- Live browser test: (-8.2652558333, -67.6735275) opened
  AM-1300706-111C0E910ABA41318B276FFC8663B290.
- Both tests used registration search with a fresh browser context and checked
  the code visible in the details panel. No map-positioning script was used.
- This update addresses property selection. CAPTCHA and download behavior have
  not been changed or validated by these tests.
- The cause of the earlier D9B7 result is not established by this change.

---

## Historical validation (previous implementation)

# Validation — 2026-11-15

Language update:

- Eleven offline tests pass, including switching English ↔ Brazilian Portuguese
  during loading while preserving inputs/disabled controls, restoring saved
  language preferences, localized validation, and translation-key parity.
- Session and error dialogs use application-owned buttons so their language
  follows the selected UI language rather than the Windows language.

Desktop UI update:

- Eight offline tests pass: coordinate parsing and GUI validation, retry after
  failure, cancellation state, and both Yes/No session-completion choices.
- Live `gui_worker` test confirmed Chromium is minimized during loading,
  restores to a normal visible window after the sample's details are verified,
  and emits the closed event after its last page closes.
- The live result matched the same expected CAR registration below.
- Native UI inspection checked the form, loading state, progress controls, and
  compact two-column step list. [gui-browser-result.png](../assets/gui-browser-result.png)
  records the live handoff.
- Desktop launcher: `start_gui.bat`. Existing CLI: `start.bat`.

Environment: Windows, Python 3.14.9, Playwright 1.65.2, bundled Chromium.

Passed:

- Decimal/DMS coordinate parsing, hemispheres, range checks, invalid input.
- Live portal navigation with latitude `-8.265255833333333` and longitude
  `-67.6735275`, without entering a CAR registration.
- The portal's coordinate lookup request carried those exact values and returned
  HTTP 200. The details panel showed
  `AM-1300706-111C0E910ABA41318B276FFC8663B290`.
- The blue details button was clicked and the details panel was visible.
- The interactive CLI accepted both prompt inputs, completed successfully,
  remained running for manual browser use, and exited with code 0 after Enter.

Evidence: [sample-result.png](../assets/sample-result.png) and
[demo.webm](../assets/demo.webm) (actual browser recording).
The video demonstrates portal navigation; CLI prompt/lifetime behavior was
tested separately. Only the supplied parcel was verified against the live site;
this is not a guarantee of coverage for every location or overlapping parcel.
