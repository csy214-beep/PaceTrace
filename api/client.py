import hashlib
import json
import logging
import os
from urllib.parse import urlencode, urlparse, parse_qs

import requests

APPKEY = os.environ["APPKEY"]
APPSECRET = os.environ["APPSECRET"]
BASE_URL = os.environ["BASE_URL"]
UA = os.environ["UA"]

_logger = logging.getLogger("unirun.api")
_logger.setLevel(logging.DEBUG)

_token = ""
_session = requests.Session()
_config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".data")
os.makedirs(_config_dir, exist_ok=True)


def _load_token():
    global _token
    path = os.path.join(_config_dir, ".token")
    if os.path.exists(path):
        with open(path) as f:
            _token = f.read().strip()


def _save_token(token: str):
    global _token
    _token = token
    path = os.path.join(_config_dir, ".token")
    with open(path, "w") as f:
        f.write(token)


def set_token(token: str):
    _save_token(token)


def get_token():
    return _token


def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _md5_upper(s: str) -> str:
    return md5(s).upper()


def _build_sign(method: str, url: str, body_str: str = None) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    flat = {k: v[0] for k, v in sorted(params.items()) if v[0]}
    parts = [f"{k}{v}" for k, v in flat.items()]
    parts.append(APPKEY)
    parts.append(APPSECRET)
    if body_str and method.upper() in ("POST", "PUT", "PATCH"):
        parts.append(body_str)
    return _md5_upper("".join(parts))


def _request(method: str, path: str, params: dict = None, body: dict = None) -> dict:
    url = BASE_URL.rstrip("/") + "/" + path.lstrip("/")
    if params:
        url += "?" + urlencode(sorted(params.items()))

    body_str = None
    if body is not None:
        body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False)

    sign = _build_sign(method, url, body_str)
    headers = {"appKey": APPKEY, "sign": sign, "User-Agent": UA}
    if _token:
        headers["token"] = _token

    _logger.info(">> %s %s", method, url)
    if body_str:
        _logger.debug("   body: %s", body_str[:200])

    if body_str:
        headers["Content-Type"] = "application/json; charset=UTF-8"
        r = _session.request(method, url, headers=headers, data=body_str.encode("utf-8"))
    else:
        r = _session.request(method, url, headers=headers)

    try:
        data = r.json()
        code = data.get("code")
        msg = data.get("msg", "")
        _logger.info("<< %s status=%s code=%s msg=%s", method, r.status_code, code, msg)
        if data.get("response") is not None:
            _logger.debug("   response: %s", json.dumps(data["response"], ensure_ascii=False)[:300])
        return data
    except Exception:
        _logger.warning("<< %s status=%s not json: %s", method, r.status_code, r.text[:200])
        raise


def get(path: str, params: dict = None) -> dict:
    return _request("GET", path, params=params)


def post(path: str, body: dict = None) -> dict:
    return _request("POST", path, body=body)


_load_token()
