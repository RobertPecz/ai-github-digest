"""Shared JSON HTTP transport."""
import requests


def request_json(method, url, *, headers=None, params=None, data=None, timeout=30):
    response = requests.request(
        method, url, headers=headers, params=params, json=data, timeout=timeout
    )
    if not response.ok:
        raise RuntimeError(
            f"{method} request failed (HTTP {response.status_code}): {response.text[:300]}"
        )
    return response.json()
