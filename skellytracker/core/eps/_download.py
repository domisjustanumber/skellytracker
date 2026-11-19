"""The download engine of the EP store. It uses only the standard library.

- Only `https`. `http` is accepted only for the loopback host, for a local index of a test. A
  redirect obeys the same rule, and a redirect from `https` to an other scheme is an error.
- The sha256 of the lock is the gate. A file with a different sha256 is deleted.
- A download that stops keeps its partial file. The next call resumes it with a byte range. If the
  server does not resume, the download starts again from byte 0.
- TLS uses `SSL_CERT_FILE` or `SSL_CERT_DIR`, else the system trust store. There is no `certifi`.
- The proxy is the system proxy setting that `urllib` reads. There is no PAC file support.
"""

import hashlib
import http.client
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

from skellytracker.core.eps import store

CHUNK = 1 << 16
WAITS = (1, 2, 4, 8, 16)  # seconds before each new attempt
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
LINUX_BUNDLES = ("/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt",
                 "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", "/etc/ssl/ca-bundle.pem")


class DownloadError(Exception):
    """A download that failed. `code` is `offline`, `http-error` or `hash-mismatch`."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class CancelledError(Exception):
    """The caller set the cancel event. The partial file stays for a resume."""


def trust_store_source(environ=os.environ, exists=os.path.exists) -> tuple[str, str | None]:
    """Where the TLS roots come from: `(kind, path)`. A frozen app has no usable OpenSSL default paths."""
    if environ.get("SSL_CERT_FILE") or environ.get("SSL_CERT_DIR"):
        return "environment", environ.get("SSL_CERT_FILE") or environ.get("SSL_CERT_DIR")
    if sys.platform == "linux":
        bundle = next((path for path in LINUX_BUNDLES if exists(path)), None)
        if bundle is not None:
            return "bundle", bundle
    return "system", None


def ssl_context() -> ssl.SSLContext:
    kind, path = trust_store_source()
    if kind == "environment":
        return ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE"), capath=os.environ.get("SSL_CERT_DIR"))
    return ssl.create_default_context(cafile=path)


def check_url(url: str) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost")):
        raise DownloadError("http-error", f"the URL is not https: {parts.scheme}://{parts.hostname}")


class HttpsRedirectHandler(urllib.request.HTTPRedirectHandler):
    """A redirect must go to an URL that `check_url` accepts, and never from `https` to an other scheme."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # `newurl` is absolute: urllib joins it first
        scheme = urllib.parse.urlsplit(newurl).scheme
        if urllib.parse.urlsplit(req.full_url).scheme == "https" and scheme != "https":
            raise DownloadError("http-error", f"a redirect from https to {scheme}")
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _attempt(opener, url: str, part: Path, cancel, progress, timeout: float) -> None:
    """One request. It appends to `part` after a 206 answer and starts `part` again after a 200 answer."""
    note_path = part.with_name(part.name + ".json")
    note = store.read_json(note_path) or {}
    have = part.stat().st_size if part.exists() else 0
    request = urllib.request.Request(url)  # noqa: S310 - check_url() accepted the scheme
    if have and note.get("url") == url and note.get("validator"):
        request.add_header("Range", f"bytes={have}-")
        request.add_header("If-Range", note["validator"])
    else:
        have = 0
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        if error.code == 416 and have:  # the file is complete already; the hash check decides
            return
        raise
    with response:
        resumed = response.status == 206 and have > 0
        if not resumed:
            have = 0
        length = response.headers.get("Content-Length", "")
        expected = have + int(length) if length.isdigit() else None
        store.write_json(note_path, {"url": url, "validator": response.headers.get("ETag") or response.headers.get("Last-Modified")})
        with open(part, "ab" if resumed else "wb") as handle:
            while True:
                if cancel is not None and cancel.is_set():
                    raise CancelledError(url)
                chunk = response.read(CHUNK)
                if not chunk:
                    if expected is not None and have < expected:
                        raise ConnectionError("the connection closed before the end of the file")
                    return
                handle.write(chunk)
                have += len(chunk)
                if progress is not None:
                    progress(have)


def fetch(url: str, sha256: str, part: Path, *, cancel=None,
          progress: Callable[[int], None] | None = None, opener=None, sleep=time.sleep, timeout: float = 60.0) -> Path:
    """Download `url` to the partial file `part`, and check its sha256. It returns `part`.

    It makes up to 5 new attempts after a connection error, a timeout or the HTTP status 408, 429 or
    5xx. A sha256 mismatch deletes the file and starts one time again from byte 0. A second mismatch
    raises `DownloadError("hash-mismatch")`.
    """
    check_url(url)
    part.parent.mkdir(parents=True, exist_ok=True)
    if opener is None:
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context()), HttpsRedirectHandler())
    failures, mismatches = 0, 0
    while True:
        try:
            _attempt(opener, url, part, cancel, progress, timeout)
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_STATUS or failures >= len(WAITS):
                raise DownloadError("http-error", f"HTTP {error.code} for {urllib.parse.urlsplit(url).hostname}") from error
            retry_after = error.headers.get("Retry-After", "") if error.headers else ""
            sleep(min(60, int(retry_after)) if retry_after.isdigit() else WAITS[failures])
            failures += 1
            continue
        except (urllib.error.URLError, http.client.HTTPException, OSError) as error:  # a connection error or a timeout: the partial file stays
            if failures >= len(WAITS):
                raise DownloadError("offline", f"no connection to {urllib.parse.urlsplit(url).hostname}: {error}") from error
            sleep(WAITS[failures])
            failures += 1
            continue
        if sha256_of(part) == sha256:
            part.with_name(part.name + ".json").unlink(missing_ok=True)
            return part
        part.unlink()
        mismatches += 1
        if mismatches > 1:
            raise DownloadError("hash-mismatch", f"the sha256 of {Path(urllib.parse.urlsplit(url).path).name} is not the sha256 of the lock")
