"""Resolve coordinates via CAR's API, then open and verify that registration."""
import re
from typing import Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from .car_api import BASE_URL, PortalError, lookup_property, normalize_registration

URL = BASE_URL + '/'
REGISTRATION = re.compile(r'[A-Z]{2}-\d{7}-[A-Fa-f0-9.]{32,}')

def verify_registration(actual: str, expected: str) -> str:
    actual = normalize_registration(actual)
    expected = normalize_registration(expected)
    if actual != expected:
        raise PortalError(f'Property mismatch: API selected {expected}, but the website displayed {actual}.')
    return actual

def open_property(page: Page, latitude: float, longitude: float, timeout: int = 90,
                  progress: Callable[[str, str], None] | None = None,
                  on_selected=None) -> str:
    def report(stage: str, message: str) -> None:
        if progress:
            progress(stage, message)
        else:
            print(message, flush=True)

    page.set_default_timeout(timeout * 1000)
    report('coordinates', 'Looking up the exact coordinates in the CAR service...')
    selected = lookup_property(page.context.request, latitude, longitude, timeout)
    report('website', 'Opening the public CAR website...')
    page.goto(URL, wait_until='domcontentloaded')
    report('map', 'Waiting for the search form to finish loading...')
    field = page.locator('.number-car input')
    field.wait_for(state='visible')
    page.locator('.el-loading-mask.is-fullscreen').wait_for(state='hidden')
    # Use the site's registration search; do not interact with map internals.
    report('property', f'Searching for CAR {selected.registration}...')
    field.fill(selected.registration)
    verify_registration(field.input_value(), selected.registration)
    try:
        with page.expect_response(
            lambda response: '/api/totalizer/getDeatilsByIdentifier/' in response.url,
            timeout=timeout * 1000,
        ) as pending:
            page.get_by_role('button', name='Buscar', exact=True).click()
        response = pending.value
        if response.status != 200:
            raise PortalError(f'Registration search returned HTTP {response.status}.')
        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalError('Registration search returned an invalid JSON response.') from exc
        if not isinstance(payload, dict):
            raise PortalError('Registration search did not return property details.')
        verify_registration(payload.get('codeProperty'), selected.registration)
        page.locator('.el-loading-mask.is-fullscreen').wait_for(state='hidden')
        details = page.locator('.el-menu-vertical-by-car')
        registration = details.get_by_text(REGISTRATION).first
        registration.wait_for(state='visible')
        verify_registration(registration.inner_text(), selected.registration)
        report('details', 'Opening and verifying the matching property details...')
        page.get_by_role('button', name='Ver Detalhes do Imóvel', exact=True).click()
        details.scroll_into_view_if_needed()
        verified = verify_registration(registration.inner_text(), selected.registration)
        if on_selected:
            on_selected(selected)
        return verified
    except PlaywrightTimeout as exc:
        raise PortalError('The website did not open the matching registration in time.') from exc
