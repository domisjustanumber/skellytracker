"""The term check of ``check_private_data.py`` lets one reviewed address through (ADR-Y14H item 12).

The bootstrap kit does not copy this file: the address belongs only to this repository. The tests use
a fake term and a fake address, so that they do not depend on the local file ``.private-terms``.
"""

from __future__ import annotations

from urllib.parse import urlsplit

import check_private_data as cpd
import pytest

TERM = "gera" + "ld"
URL = "https://models.example.org/" + TERM + "/suite-models/"
AT = "@"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (URL + "resolve/0123abcd/model_fp32.onnx", []),
        ('{path: a.onnx, url: "' + URL + 'resolve/0123abcd/a.onnx", bytes: 1}', []),
        ("the files of " + TERM, ["private term"]),
        ("https://models.example.org/" + TERM + "/other-models/a.onnx", ["private term"]),
        (URL + "a.onnx, uploaded by " + TERM, ["private term"]),
        (URL + "resolve/" + TERM + ".onnx", ["private term"]),
        ("https://models.example.org/" + TERM + "/suite-models-x/a.onnx", ["private term"]),
        ("https://models.example.com/" + TERM + "/suite-models/a.onnx", ["private term"]),
        ("http://models.example.org/" + TERM + "/suite-models/a.onnx", ["private term"]),
        ("https://models.example.org/" + TERM + "/suite-models", ["private term"]),
        (TERM[:3] + URL + TERM[3:], []),
        (URL + "a.onnx " + TERM + AT + "gmail.com", ["email address", "private term"]),
    ],
)
def test_allowed_url_is_taken_out_of_the_term_check_only(
    monkeypatch: pytest.MonkeyPatch, text: str, expected: list[str]
) -> None:
    monkeypatch.setattr(cpd, "ALLOWED_TERM_URL", URL)
    assert [f.kind for f in cpd.scan_text("doc.md", text, [TERM])] == expected


def test_allowed_url_is_one_repository_of_one_public_host() -> None:
    url = urlsplit(cpd.ALLOWED_TERM_URL)
    assert (url.scheme, url.netloc, url.query, url.fragment) == ("https", "huggingface.co", "", "")
    assert url.path.endswith("/")
    assert url.path.strip("/").split("/")[1:] == ["skellytracker-certify-models"]
