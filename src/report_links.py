"""Open the public statement route in the user's default browser."""
import webbrowser

from .car_api import normalize_registration


def statement_url(registration: str) -> str:
    return "https://www.car.gov.br/#/consultar/" + normalize_registration(registration)


def open_statement(registration: str) -> None:
    url = statement_url(registration)
    if not webbrowser.open(url, new=1):
        raise OSError("Could not find or launch the default web browser.")
