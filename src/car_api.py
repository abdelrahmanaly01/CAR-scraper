"""Coordinate lookup service, independent of the map and desktop UI."""
from dataclasses import dataclass
import math
import re
from playwright.sync_api import APIRequestContext, Error as PlaywrightError

BASE_URL = 'https://consulta.car.gov.br'

class PortalError(RuntimeError):
    pass

def normalize_registration(value: str) -> str:
    if not isinstance(value, str):
        raise PortalError('The CAR service returned an invalid registration.')
    code = value.strip().upper().replace('.', '')
    if not re.fullmatch(r'[A-Z]{2}-\d{7}-[A-F0-9]{32}', code):
        raise PortalError('The CAR service returned an invalid registration.')
    return code

@dataclass(frozen=True)
class Property:
    registration: str
    id_origin: int | None = None

def lookup_property(request: APIRequestContext, latitude: float, longitude: float,
                    timeout: int = 90) -> Property:
    if (not math.isfinite(latitude) or not math.isfinite(longitude)
            or not -90 <= latitude <= 90 or not -180 <= longitude <= 180):
        raise PortalError('Invalid latitude or longitude.')
    try:
        response = request.get(
            BASE_URL + '/api/totalizer/getDetailsByCoordinates',
            params={'lat': latitude, 'lng': longitude}, timeout=timeout * 1000,
        )
    except PlaywrightError as exc:
        raise PortalError(f'Coordinate lookup failed: {exc}') from exc
    try:
        if response.status == 204:
            raise PortalError('No CAR property was returned for these coordinates.')
        if response.status != 200:
            raise PortalError(f'Coordinate lookup returned HTTP {response.status}.')
        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalError('Coordinate lookup returned an invalid JSON response.') from exc
        if payload is None or payload == {}:
            raise PortalError('No CAR property was returned for these coordinates.')
        if not isinstance(payload, dict):
            raise PortalError('Coordinate lookup returned an unexpected response.')
        origin = payload.get('idOrigin')
        if type(origin) is not int or origin <= 0:
            origin = None
        return Property(normalize_registration(payload.get('codeProperty')), origin)
    finally:
        response.dispose()
