#!/usr/bin/env python3
"""Privacy guard for the public vancouver-room-hunt repo.

Fails when a tracked file contains Hangul, an email address, a phone number,
an amount in Korean won, a URL outside the allowlist, or a deny-listed term; when a file
cannot be read as text; when a path is outside the expected layout; or when a
path itself matches a rule. Reports the file, line and rule only. The matched
text is never printed, and a path that is itself a finding is withheld, so CI
logs cannot leak what the guard caught.

Modes: the tracked snapshot in the index (default), the staged changes
(--staged, pre-commit), a commit message (--message FILE, commit-msg), every
commit and its message in a range (--history BASE..HEAD, CI), and the commits
a push would publish (--pre-push, reads the pre-push hook's stdin).
"""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

RULES = [
    ("hangul", re.compile(
        r"[\u1100-\u11FF\u3130-\u318F\u3200-\u321E\u3260-\u327E\uA960-\uA97F"
        r"\uAC00-\uD7AF\uD7B0-\uD7FF\uFFA0-\uFFDC]")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    # North American numbers (area and exchange start with 2-9), Korean mobiles with or
    # without +82, and Korean landlines. Digit runs inside longer ids or hashes never match.
    ("phone", re.compile(
        r"(?<![\w-])(?:\+?1[ .-]?)?\(?[2-9]\d{2}\)?[ .-]?[2-9]\d{2}[ .-]?\d{4}(?![\w-])"
        r"|(?<![\w-])(?:\+82[ .-]?1[016789]|01[016789])[ .-]?\d{3,4}[ .-]?\d{4}(?![\w-])"
        r"|(?<![\w-])0\d{1,2}-\d{3,4}-\d{4}(?![\w-])")),
    # Room prices and fares in CAD are market data and are the point of this repo, so dollar
    # amounts pass. The trade-off: a personal CAD figure (a balance, a salary, the rent
    # actually paid) has no rule of its own here, so every such figure must be on the private
    # deny-list. Won amounts are the owner's own finances and never belong here. A lone
    # "won" after a small number is a verb, so it needs a real amount.
    ("krw", re.compile(
        r"\u20A9\s?\d"
        r"|\bKRW\s?\d"
        r"|\d[\d,.]*\s?KRW\b"
        r"|(?:\d{1,3}(?:,\d{3})+|\d{4,})\s?won\b"
        r"|\d[\d.,]*\s?(?:k|m|thousand|million)\s?won\b", re.IGNORECASE)),
]
URL = re.compile(r"https?://[^\s)>\]\"'`]+", re.IGNORECASE)
# A link written without a scheme (a domain followed by a path) is still a link.
BARE_DOMAIN = re.compile(
    r"(?<![\w@./:-])(?:[a-z0-9-]+\.)+(?:com|net|org|io|ca|kr|co|dev|app|me|ai|gg|ly|so|xyz|info|biz)"
    r"/[^\s)>\]\"'`]*", re.IGNORECASE)
# (exact host, path prefix). A prefix matches whole path segments only.
ALLOWED_URLS = (
    ("github.com", "/bnivibe/vancouver-room-hunt"),
    ("docs.claude.com", ""),
    ("www.anthropic.com", ""),
    # Listing sources
    ("vancouver.craigslist.org", ""),
    ("www.craigslist.org", ""),
    ("www.kijiji.ca", ""),
    ("www.facebook.com", "/marketplace"),
    ("www.facebook.com", "/groups"),
    ("cafe.daum.net", ""),
    ("m.cafe.daum.net", ""),
    ("cafe.naver.com", ""),
    ("m.cafe.naver.com", ""),
    ("apis.naver.com", ""),
    ("search.naver.com", ""),
    ("www.vanchosun.com", ""),
    ("rentals.ca", ""),
    ("liv.rent", ""),
    # Public records, maps and routing
    ("www.bcassessment.ca", ""),
    ("ltsa.ca", ""),
    ("www.ltsa.ca", ""),
    ("geodash.vpd.ca", ""),
    ("opendata.vancouver.ca", ""),
    ("routing.openstreetmap.de", ""),
    ("overpass-api.de", ""),
    ("overpass.kumi.systems", ""),
    ("nominatim.openstreetmap.org", ""),
    # Directions only. Street addresses are caught by the deny-list, not by this rule.
    ("www.google.com", "/maps/dir"),
    ("www.youtube.com", "/oembed"),
    ("i.ytimg.com", ""),
    # Fares and law
    ("www.translink.ca", ""),
    ("www.bclaws.gov.bc.ca", ""),
    ("www2.gov.bc.ca", ""),
    ("civilresolutionbc.ca", ""),
    ("decisions.civilresolutionbc.ca", ""),
    ("discord.com", "/api"),
)
# A Discord webhook URL is a credential: anyone holding it can post to the channel.
DISCORD_HOSTS = {"discord.com", "discordapp.com", "ptb.discord.com", "canary.discord.com"}
# Every tracked path must match one of these. A transcript saved into the clone by
# mistake is then an unexpected path, whatever its words are.
EXPECTED_PATHS = (
    "README.md", "FIELD-NOTES.md", "LICENSE", ".gitignore",
    "skill/SKILL.md", "skill/profile.example.md", "skill/references/*.md",
    "skill/scripts/*.py", "skill/tests/*.py", "skill/examples/*.json",
    "guard/check_public.py", "guard/install-hooks.sh", "guard/tests/*.py",
    ".github/workflows/*.yml",
)
DEFAULT_DENYLIST = Path.home() / ".claude" / "room-hunt-denylist.txt"
ZERO = "0" * 40


def deny_pattern(term):
    # Words may be split by a line wrap or markdown emphasis (**Jane** Doe).
    words = [re.escape(w) for w in term.split()]
    return re.compile(r"(?<![A-Za-z0-9])" + r"[\s*_]+".join(words) + r"(?![A-Za-z0-9])", re.IGNORECASE)


def url_allowed(url):
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return False
    path = parts.path
    if host in DISCORD_HOSTS and "/webhooks/" in path + "/":
        return False
    for allowed_host, prefix in ALLOWED_URLS:
        if host == allowed_host and (not prefix or path == prefix or path.startswith(prefix + "/")):
            return True
    return False


def scan_text(path, text, deny):
    found = []
    for no, line in enumerate(text.splitlines(), start=1):
        for name, rx in RULES:
            if rx.search(line):
                found.append((path, no, name))
        urls = URL.findall(line) + ["https://" + bare for bare in BARE_DOMAIN.findall(line)]
        # Trailing punctuation belongs to the sentence, not the link.
        if any(not url_allowed(url.rstrip(".,;:!?")) for url in urls):
            found.append((path, no, "url"))
    # Deny terms run over the whole text so a term split across lines is still caught.
    hit_lines = set()
    for rx in (deny_pattern(t) for t in deny):
        for m in rx.finditer(text):
            hit_lines.add(text.count("\n", 0, m.start()) + 1)
    found.extend((path, no, "denylist") for no in sorted(hit_lines))
    found.sort(key=lambda f: f[1])
    return found


TRAILER = re.compile(r"^[A-Za-z][A-Za-z-]*-by:\s", re.IGNORECASE)


def scan_message(label, text, deny):
    """Commit messages are public too. Trailers (author identities) and git comment lines are skipped."""
    kept = "\n".join("" if line.startswith("#") or TRAILER.match(line) else line for line in text.splitlines())
    return scan_text(label, kept, deny)


def path_rules(path, deny):
    rules = [name for name, rx in RULES if rx.search(path)]
    words = re.sub(r"[-_./]+", " ", path)
    if any(deny_pattern(t).search(path) or deny_pattern(t).search(words) for t in deny):
        rules.append("denylist")
    if not any(fnmatch.fnmatchcase(path, pattern) for pattern in EXPECTED_PATHS):
        rules.append("unexpected-path")
    return rules


def decode(raw):
    """Return (text, undecodable). UTF-16 with a byte-order mark is read; anything else must be UTF-8."""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return raw.decode("utf-16"), False
        except UnicodeDecodeError:
            return None, True
    if b"\x00" in raw:
        return None, True
    try:
        return raw.decode("utf-8"), False
    except UnicodeDecodeError:
        return None, True


def scan_blobs(items, deny, prefix=""):
    """Scan (path, raw bytes) pairs. A file that cannot be read as text is a finding, not a skip."""
    found = []
    for n, (path, raw) in enumerate(items, start=1):
        hits = path_rules(path, deny)
        label = f"{prefix}path #{n} (withheld)" if hits else f"{prefix}{path}"
        found.extend((label, 0, rule) for rule in hits)
        text, undecodable = decode(raw)
        if undecodable:
            found.append((label, 0, "undecodable"))
            continue
        found.extend((label, no, rule) for (_p, no, rule) in scan_text(path, text, deny))
    return found


def format_findings(found):
    return [f"{path}: {rule}" if no == 0 else f"{path}:{no}: {rule}" for (path, no, rule) in found]


def load_denylist():
    env = os.environ.get("DENYLIST")
    if env:
        source = env
    else:
        path = Path(os.environ.get("ROOM_HUNT_DENYLIST", DEFAULT_DENYLIST)).expanduser()
        if not path.is_file():
            print(f"guard: deny-list missing ({path}). Create it or set DENYLIST.", file=sys.stderr)
            raise SystemExit(2)
        source = path.read_text(encoding="utf-8")
    terms = []
    for line in source.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    if not terms:
        print("guard: deny-list has no terms. Refusing to run with the name check switched off.", file=sys.stderr)
        raise SystemExit(2)
    return terms


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def split_z(out):
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def tracked_files(staged):
    if staged:
        return split_z(git("diff", "--cached", "--name-only", "-z", "--diff-filter=d"))
    return split_z(git("ls-files", "-z"))


def read(path):
    # The index, not the working tree: no symlink is followed, and a file deleted
    # locally but still tracked does not crash the run.
    return git("show", f":{path}")


def history_findings(rev_args, deny):
    """Scan every file each commit in the range adds or changes, so a leak removed later still fails."""
    found = []
    for sha in git("rev-list", *rev_args).decode().split():
        out = git("diff-tree", "-r", "--root", "-m", "--no-commit-id", "--name-only", "-z", "--diff-filter=d", sha)
        paths = list(dict.fromkeys(split_z(out)))
        found.extend(scan_blobs([(p, git("show", f"{sha}:{p}")) for p in paths], deny, prefix=f"{sha[:7]} "))
        message = git("log", "-1", "--format=%B", sha).decode("utf-8", "replace")
        found.extend(scan_message(f"{sha[:7]} commit message", message, deny))
    return found


def pre_push_revs(text):
    """Rev-list arguments for each ref in the pre-push hook's stdin."""
    revs = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        _local_ref, local_sha, _remote_ref, remote_sha = parts
        if local_sha == ZERO:
            continue  # a branch deletion publishes nothing
        revs.append([local_sha, "--not", "--remotes"] if remote_sha == ZERO else [f"{remote_sha}..{local_sha}"])
    return revs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Privacy guard for the public repo")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="scan the staged snapshot (pre-commit)")
    mode.add_argument("--history", metavar="REVS", help="scan every commit in a range, e.g. BASE..HEAD")
    mode.add_argument("--pre-push", action="store_true", help="scan the commits a push would publish")
    mode.add_argument("--message", metavar="FILE", help="scan a commit message file (commit-msg hook)")
    args = ap.parse_args(argv)
    deny = load_denylist()
    if args.message:
        text = Path(args.message).read_text(encoding="utf-8", errors="replace")
        found = scan_message("commit message", text, deny)
    elif args.history or args.pre_push:
        ranges = [args.history.split()] if args.history else pre_push_revs(sys.stdin.read())
        found = []
        for rev_args in ranges:
            found.extend(history_findings(rev_args, deny))
    else:
        found = scan_blobs([(p, read(p)) for p in tracked_files(args.staged)], deny)
    for line in format_findings(found):
        print(line)
    print(f"guard: {len(found)} finding(s), {len(deny)} deny-list term(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
