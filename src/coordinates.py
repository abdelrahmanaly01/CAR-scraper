"""Validate decimal degrees or degrees/minutes/seconds without dependencies."""
import math
import re


def parse_coordinate(value: str, axis: str) -> float:
    if axis not in {"latitude", "longitude"}:
        raise ValueError("Unknown coordinate axis")
    text = value.strip().upper().replace(",", ".")
    hemisphere = text[-1:] if text[-1:] in {"N", "S", "E", "W"} else ""
    if hemisphere:
        if hemisphere not in ("NS" if axis == "latitude" else "EW"):
            raise ValueError(f"Wrong hemisphere for {axis}")
        text = text[:-1].strip()
    # Accept decimal or DMS, but reject stray letters and missing numbers.
    parts = re.fullmatch(
        r'([+-]?\d+(?:\.\d+)?)\s*(?:[°\s]\s*(\d+(?:\.\d+)?)\s*'
        r'(?:[\x27′\s]\s*(\d+(?:\.\d+)?)\s*[\x22″]?)?)?\s*', text
    )
    if not parts:
        raise ValueError("Use decimal degrees or DMS, e.g. -8.2652558333 or 8°15\x2754.921\x22S")
    degrees = float(parts[1])
    minutes = float(parts[2] or 0)
    seconds = float(parts[3] or 0)
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Minutes and seconds must be less than 60")
    if parts[2] and not degrees.is_integer():
        raise ValueError("DMS degrees must be an integer")
    negative = text.startswith("-")
    if hemisphere and negative and hemisphere in "NE":
        raise ValueError("Negative sign conflicts with N/E hemisphere")
    result = abs(degrees) + minutes / 60 + seconds / 3600
    if negative or hemisphere in {"S", "W"}:
        result = -result
    limit = 90 if axis == "latitude" else 180
    if not math.isfinite(result) or abs(result) > limit:
        raise ValueError(f"{axis} must be between {-limit} and {limit}")
    return result
