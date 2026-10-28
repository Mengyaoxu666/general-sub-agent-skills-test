"""Offline allowlist and heuristic privacy check. Findings never echo matched values.

This is defense in depth, not a complete secret detector or a privacy guarantee.
Run from any directory; --staged checks the actual Git index instead of disk.
"""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "release-manifest.json"
PATTERNS = {
    "private-key-marker": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "typical-secret": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b"),
    "email-address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "windows-absolute-path": re.compile(r"\b[A-Za-z]:[\\/][^\s\"'<>]+"),
    "unix-personal-path": re.compile(r"/(?:home|Users|root|mnt|private)/[A-Za-z0-9_.-]+(?:/|\b)"),
    "ip-address": re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])"),
    "raw-session-identifier": re.compile(r"\b(?:ses_|msg_)[A-Za-z0-9]{12,}\b"),
    "credential-url": re.compile(r"https?://[^\s/@]+:[^\s/@]+@", re.I),
    "subscription-url": re.compile(r"(?:vmess|vless|trojan|ss|ssr)://", re.I),
    "credential-assignment": re.compile(r"(?:api[_-]?key|access[_-]?token|password|secret)\s*[\"']?\s*[:=]\s*[\"'][^\"'\r\n]{12,}[\"']", re.I),
}


def allowed_url(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.username or parts.password or parts.port:
        return False
    if parts.query or parts.fragment:
        return False
    if parts.hostname == "opencode.ai":
        return parts.path.startswith("/v2/docs/")
    if parts.hostname == "github.com":
        return parts.path == "/obra/superpowers" or parts.path.startswith("/obra/superpowers/blob/")
    return False


def scan_text(text):
    findings = []
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append({"line": text.count("\n", 0, match.start()) + 1, "rule": name})
    for match in re.finditer(r"https?://[^\s<>\"'`()，。；]+", text):
        url = match.group().rstrip(").,;，。；")
        try:
            allowed = allowed_url(url)
        except ValueError:
            allowed = False
        if not allowed:
            findings.append({"line": text.count("\n", 0, match.start()) + 1, "rule": "unapproved-external-url"})
    return findings


def git(*arguments):
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=True)
    return result.stdout


def valid_release_path(path):
    value = PurePosixPath(path)
    return not value.is_absolute() and ".." not in value.parts and "\\" not in path and path == value.as_posix()


def inspect(staged=False):
    problems = []
    raw = git("show", ":" + MANIFEST) if staged else (ROOT / MANIFEST).read_bytes()
    manifest = json.loads(raw)
    expected = manifest["files"]
    if not isinstance(expected, list) or len(set(expected)) != len(expected) or not all(isinstance(p, str) and valid_release_path(p) for p in expected):
        raise ValueError("Unsafe manifest")
    if staged:
        actual = set(git("ls-files", "-z").decode("utf-8").split("\0")) - {""}
    else:
        actual = set()
        for path in ROOT.rglob("*"):
            relative = path.relative_to(ROOT)
            if any(part in (".git", "__pycache__") for part in relative.parts):
                continue
            if path.is_symlink():
                problems.append({"file": "[unlisted path]", "rule": "symbolic-link"})
            if path.is_file():
                actual.add(relative.as_posix())
    if actual != set(expected):
        problems.append({"file": MANIFEST, "rule": "release-file-set-mismatch"})
    for name in expected:
        if name not in actual:
            continue
        if staged:
            mode = git("ls-files", "--stage", "--", name).decode("utf-8").split()[0]
            if mode not in ("100644", "100755"):
                problems.append({"file": name, "rule": "nonregular-index-entry"})
            data = git("show", ":" + name)
        else:
            data = (ROOT / name).read_bytes()
        if len(data) > 131072 or b"\x00" in data:
            problems.append({"file": name, "rule": "oversized-or-binary"})
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append({"file": name, "rule": "non-utf8"})
            continue
        problems.extend({"file": name, **issue} for issue in scan_text(text))
    return {"checked_files": len(expected), "source": "git-index" if staged else "working-files", "problems": problems}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true", help="Scan exactly the tracked index blobs")
    args = parser.parse_args()
    try:
        result = inspect(args.staged)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        parser.exit(2, "Release verification could not complete; no input content is echoed.\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(bool(result["problems"]))


if __name__ == "__main__":
    main()
