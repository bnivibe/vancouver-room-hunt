import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_public as cp  # noqa: E402

# Fixtures are assembled at runtime so this file itself passes the guard.
HANGUL = chr(0xD55C) + chr(0xAE00)
EMAIL = "someone" + "@" + "example.org"
SHORT_EMAIL = "a" + "@" + "b.co"
NA_PHONE = "-".join(["604", "334", "9304"])
KR_PHONE = "-".join(["010", "1234", "5678"])
HTTPS = "https" + "://"


class ScanText(unittest.TestCase):
    def rules(self, text, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_text("x.md", text, list(deny))]

    def test_clean_text_passes(self):
        self.assertEqual(self.rules("A plain English line.\nAnother one."), [])

    def test_hangul_fails(self):
        self.assertEqual(self.rules("hello " + HANGUL), ["hangul"])

    def test_email_fails(self):
        self.assertEqual(self.rules("write to " + EMAIL + " today"), ["email"])

    def test_phone_formats_fail(self):
        for text in ["call " + NA_PHONE, "call (604) 334 " + "9304", "call +1 604.334." + "9304", "call " + KR_PHONE]:
            self.assertEqual(self.rules(text), ["phone"], text)

    def test_dates_and_versions_are_not_phones(self):
        self.assertEqual(self.rules("on 2026-10-14 we used v1.2.3"), [])

    def test_won_amounts_fail(self):
        for text in ["KRW" + " 50000", "about 50000 " + "KRW", "1,000,000 " + "won", chr(0x20A9) + "1,000",
                     "1.37M " + "won", "3 million " + "won"]:
            self.assertEqual(self.rules(text), ["krw"], text)

    def test_cad_market_prices_pass(self):
        for text in ["rooms start at CAD 1,000", "a Zone 2 pass is $156.70", "about 900 dollars", "rent 850 CAD"]:
            self.assertEqual(self.rules(text), [], text)

    def test_shell_dollar_is_not_money(self):
        self.assertEqual(self.rules("cd $HOME and echo ${VAR}"), [])

    def test_url_allowlist(self):
        self.assertEqual(self.rules("see https://github.com/bnivibe/vancouver-room-hunt/blob/main/skill/SKILL.md"), [])
        self.assertEqual(self.rules("see " + HTTPS + "github" + ".com/bnivibe/other-repo"), ["url"])
        self.assertEqual(self.rules("see " + HTTPS + "example" + ".com/page"), ["url"])

    def test_denylist_case_and_possessive(self):
        self.assertEqual(self.rules("ACME called", ["Acme"]), ["denylist"])
        self.assertEqual(self.rules("Acme's team", ["Acme"]), ["denylist"])

    def test_denylist_needs_word_boundary(self):
        self.assertEqual(self.rules("a Zetaform demo", ["Zeta"]), [])

    def test_denylist_multiword_spacing(self):
        self.assertEqual(self.rules("met Jane   Doe there", ["Jane Doe"]), ["denylist"])

    def test_line_numbers(self):
        found = cp.scan_text("x.md", "ok\nok\nmail " + SHORT_EMAIL, [])
        self.assertEqual(found, [("x.md", 3, "email")])


class Reporting(unittest.TestCase):
    def test_report_never_prints_the_match(self):
        lines = cp.format_findings(cp.scan_text("x.md", "hi " + EMAIL, []))
        self.assertTrue(lines)
        self.assertNotIn(EMAIL, "\n".join(lines))
        self.assertNotIn("example", "\n".join(lines))


class Files(unittest.TestCase):
    def test_binary_is_skipped(self):
        text, skipped = cp.decode(b"\x89PNG\r\n\x1a\n\x00\xff\xfe")
        self.assertIsNone(text)
        self.assertTrue(skipped)


class Denylist(unittest.TestCase):
    def test_env_list_is_used_first(self):
        os.environ["DENYLIST"] = "Alpha Corp\n\n# comment\nBeta"
        try:
            self.assertEqual(cp.load_denylist(), ["Alpha Corp", "Beta"])
        finally:
            del os.environ["DENYLIST"]

    def test_missing_list_exits(self):
        saved = os.environ.pop("DENYLIST", None)
        os.environ["ROOM_HUNT_DENYLIST"] = "/nonexistent/denylist.txt"
        try:
            with self.assertRaises(SystemExit) as ctx:
                cp.load_denylist()
            self.assertEqual(ctx.exception.code, 2)
        finally:
            del os.environ["ROOM_HUNT_DENYLIST"]
            if saved is not None:
                os.environ["DENYLIST"] = saved


class Fixes(unittest.TestCase):
    """Final-review findings I1 to I8: every gap must fail closed."""

    def rules(self, text, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_text("x.md", text, list(deny))]

    def blob_rules(self, items, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_blobs(items, list(deny))]

    # I1: undecodable content is a finding, UTF-16 with a BOM is read
    def test_utf16_with_bom_is_decoded(self):
        self.assertEqual(cp.decode(b"\xff\xfe" + "hi there".encode("utf-16-le")), ("hi there", False))

    def test_legacy_korean_encoding_is_a_finding(self):
        self.assertEqual(self.blob_rules([("README.md", HANGUL.encode("cp949"))]), ["undecodable"])

    def test_binary_is_a_finding(self):
        self.assertEqual(self.blob_rules([("README.md", b"\x89PNG\r\n\x1a\n\x00\xff")]), ["undecodable"])

    # I3: paths are scanned and never printed when they hit
    def test_path_is_scanned_and_withheld(self):
        found = cp.scan_blobs([("lessons/acme-offer.md", b"clean")], ["Acme"])
        self.assertIn("denylist", [r for (_p, _l, r) in found])
        self.assertNotIn("acme", "\n".join(cp.format_findings(found)).lower())

    # I8: only known paths may be tracked
    def test_unexpected_path_is_a_finding_and_withheld(self):
        found = cp.scan_blobs([("notes/private-slug/thread.md", b"clean")], [])
        self.assertEqual([r for (_p, _l, r) in found], ["unexpected-path"])
        self.assertNotIn("private-slug", "\n".join(cp.format_findings(found)))

    def test_expected_paths_pass(self):
        paths = ["README.md", "FIELD-NOTES.md", "LICENSE", ".gitignore", "skill/SKILL.md",
                 "skill/profile.example.md", "skill/references/sources.md", "skill/scripts/score.py",
                 "skill/tests/test_score.py", "skill/examples/listings.example.json",
                 "guard/check_public.py", "guard/install-hooks.sh", "guard/tests/test_check_public.py",
                 ".github/workflows/guard.yml"]
        self.assertEqual(self.blob_rules([(p, b"clean") for p in paths]), [])

    # I4: a deny term split by a line wrap or markdown emphasis
    def test_denylist_across_wrap_and_emphasis(self):
        self.assertEqual(self.rules("we met Jane\nDoe there", ["Jane Doe"]), ["denylist"])
        self.assertEqual(self.rules("met **Jane** Doe", ["Jane Doe"]), ["denylist"])

    def test_wrapped_hit_reports_its_first_line(self):
        self.assertEqual(cp.scan_text("x.md", "ok\nJane\nDoe", ["Jane Doe"]), [("x.md", 2, "denylist")])

    # I5: exact hosts, segment-bounded paths, no webhook URLs
    def test_url_lookalikes_and_webhooks_fail(self):
        for url in [HTTPS + "discord" + ".com/api/webhooks/123/abc",
                    HTTPS + "discord" + ".com/api/v10/webhooks/123/abc",
                    HTTPS + "docs.claude.com.evil.example/x",
                    HTTPS + "github" + ".com/bnivibe/vancouver-room-hunt-private",
                    HTTPS + "www.facebook" + ".com/profile.php?id=1",
                    HTTPS + "www.google" + ".com/maps/place/somewhere"]:
            self.assertEqual(self.rules("see " + url), ["url"], url)

    def test_allowed_urls_pass(self):
        for url in [HTTPS + "discord.com/api/v10/channels/1/messages",
                    HTTPS + "docs.claude.com/en/docs",
                    HTTPS + "github.com/bnivibe/vancouver-room-hunt",
                    HTTPS + "vancouver.craigslist.org/search/van/roo?max_price=1300",
                    HTTPS + "www.facebook.com/marketplace/vancouver/search?query=room",
                    HTTPS + "routing.openstreetmap.de/routed-foot/route/v1/driving/1,2;3,4"]:
            self.assertEqual(self.rules("see " + url), [], url)

    def test_trailing_punctuation_is_not_part_of_the_link(self):
        self.assertEqual(self.rules("(" + HTTPS + "github.com/bnivibe/vancouver-room-hunt, 1.0)"), [])
        self.assertEqual(self.rules("see " + HTTPS + "docs.claude.com/en/docs."), [])

    # I6: an empty deny-list cannot switch layer 3 off
    def test_empty_denylist_exits(self):
        os.environ["DENYLIST"] = "# only a comment\n   \n"
        try:
            with self.assertRaises(SystemExit) as ctx:
                cp.load_denylist()
            self.assertEqual(ctx.exception.code, 2)
        finally:
            del os.environ["DENYLIST"]

    # I2: pre-push ranges
    def test_pre_push_ranges(self):
        zero = "0" * 40
        a, b = "a" * 40, "b" * 40
        self.assertEqual(cp.pre_push_revs(f"refs/heads/x {a} refs/heads/x {b}\n"), [[f"{b}..{a}"]])
        self.assertEqual(cp.pre_push_revs(f"refs/heads/x {a} refs/heads/x {zero}\n"), [[a, "--not", "--remotes"]])
        self.assertEqual(cp.pre_push_revs(f"(delete) {zero} refs/heads/x {b}\n"), [])


class History(unittest.TestCase):
    """I2: a leak added and later removed must still fail the history scan."""

    def test_removed_leak_in_history_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            def git(*args):
                return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t" + "@" + "t.invalid",
                                       "-c", "commit.gpgsign=false", *args],
                                      cwd=d, check=True, capture_output=True, text=True).stdout.strip()
            readme = Path(d) / "README.md"
            git("init", "-q")
            readme.write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            first = git("rev-parse", "HEAD")
            readme.write_text("mail " + EMAIL + "\n")
            git("commit", "-q", "-am", "two")
            readme.write_text("clean\n")
            git("commit", "-q", "-am", "three")
            saved = os.getcwd()
            os.environ["DENYLIST"] = "Zeta"
            try:
                os.chdir(d)
                found = cp.history_findings([f"{first}..HEAD"], ["Zeta"])
                self.assertEqual([r for (_p, _l, r) in found], ["email"])
                self.assertEqual(cp.main(["--history", f"{first}..HEAD"]), 1)
                self.assertEqual(cp.main([]), 0)
            finally:
                os.chdir(saved)
                del os.environ["DENYLIST"]


INSTALLER = Path(__file__).resolve().parents[1] / "install-hooks.sh"


def make_repo(d):
    def git(*args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t" + "@" + "t.invalid",
                               "-c", "commit.gpgsign=false", *args],
                              cwd=d, check=True, capture_output=True, text=True).stdout.strip()
    git("init", "-q")
    return git


class InRepo:
    """Run the guard inside a temporary repo with a made-up deny-list, output silenced."""

    def __init__(self, d, deny="Zeta"):
        self.d, self.deny = d, deny

    def __enter__(self):
        self.saved = os.getcwd()
        self.env = os.environ.get("DENYLIST")
        os.environ["DENYLIST"] = self.deny
        os.chdir(self.d)
        return self

    def __exit__(self, *exc):
        os.chdir(self.saved)
        if self.env is None:
            os.environ.pop("DENYLIST", None)
        else:
            os.environ["DENYLIST"] = self.env
        return False

    def main(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()):
            return cp.main(list(argv))


class Minors(unittest.TestCase):
    """Final-review minors M1 to M4, M10, M14, M16."""

    def rules(self, text, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_text("x.md", text, list(deny))]

    # M1
    def test_more_phone_formats_fail(self):
        for text in ["call +82 10 1234 " + "5678", "call +82-10-1234-" + "5678", "call 010 1234 " + "5678",
                     "call 0101234" + "5678", "call (604)334-" + "9304", "call 604334" + "9304"]:
            self.assertEqual(self.rules(text), ["phone"], text)

    def test_long_ids_timestamps_and_hashes_are_not_phones(self):
        for text in ["channel 98765432109876" + "54321", "epoch 17919" + "33272", "commit a60433" + "49304b"]:
            self.assertEqual(self.rules(text), [], text)

    # M2
    def test_more_won_formats_fail(self):
        for text in ["KRW" + "1000", "1,234 " + "Won", "costs 2.5k " + "won", chr(0x20A9) + " 40"]:
            self.assertEqual(self.rules(text), ["krw"], text)

    def test_positional_dollars_and_won_as_a_verb_pass(self):
        for text in ["awk '{print $1, $2}'", "echo $1 $2", "sed 's/x/$1/'", "persona 2 won the clash"]:
            self.assertEqual(self.rules(text), [], text)

    # M3
    def test_uppercase_scheme_and_bare_domains_fail(self):
        for text in ["see HTTPS" + "://example.org/page", "see linkedin" + ".com/in/jane-doe",
                     "see drive.google" + ".com/file/d/x"]:
            self.assertEqual(self.rules(text), ["url"], text)

    def test_bare_allowed_domain_and_file_names_pass(self):
        for text in ["see github" + ".com/bnivibe/vancouver-room-hunt", "run skill/scripts/score.py and guard/check_public.py",
                     "re.compile(x)", "see docs.claude" + ".com/en/docs"]:
            self.assertEqual(self.rules(text), [], text)

    # M4
    def test_halfwidth_and_enclosed_hangul_fail(self):
        for code in (0xFFA1, 0x3200, 0x3260):
            self.assertEqual(self.rules("x " + chr(code)), ["hangul"], hex(code))

    # M14
    def test_commit_message_scan_skips_trailers_and_comments(self):
        msg = "fix: drop Acme from lessons\n\n# a git comment " + EMAIL + "\nCo-Authored-By: X <" + EMAIL + ">\n"
        self.assertEqual([r for (_p, _l, r) in cp.scan_message("msg", msg, ["Acme"])], ["denylist"])

    def test_message_mode_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "COMMIT_EDITMSG"
            path.write_text("fix: mention Zeta\n")
            with InRepo(d) as repo:
                self.assertEqual(repo.main("--message", str(path)), 1)

    def test_history_scans_commit_messages(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            first = git("rev-parse", "HEAD")
            (Path(d) / "README.md").write_text("still clean\n")
            git("commit", "-q", "-am", "two: talk about Zeta")
            with InRepo(d):
                found = cp.history_findings([f"{first}..HEAD"], ["Zeta"])
            self.assertEqual([r for (_p, _l, r) in found], ["denylist"])
            self.assertTrue(found[0][0].endswith("commit message"))

    # M10, M16
    def test_main_exit_codes_on_the_tree(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("mail " + EMAIL + "\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            with InRepo(d) as repo:
                self.assertEqual(repo.main(), 1)
                (Path(d) / "README.md").write_text("clean\n")
                git("commit", "-q", "-am", "two")
                self.assertEqual(repo.main(), 0)

    def test_deleted_working_file_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            (Path(d) / "README.md").unlink()
            with InRepo(d) as repo:
                self.assertEqual(repo.main(), 0)

    def test_staged_type_change_is_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "LICENSE").write_text("clean\n")
            (Path(d) / "README.md").symlink_to("LICENSE")
            git("add", "LICENSE", "README.md")
            git("commit", "-q", "-m", "one")
            (Path(d) / "README.md").unlink()
            (Path(d) / "README.md").write_text("mail " + EMAIL + "\n")
            git("add", "README.md")
            with InRepo(d) as repo:
                self.assertEqual(repo.main("--staged"), 1)

    def test_missing_denylist_exits_2_from_main(self):
        saved = os.environ.pop("DENYLIST", None)
        os.environ["ROOM_HUNT_DENYLIST"] = "/nonexistent/denylist.txt"
        try:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
                cp.main([])
            self.assertEqual(ctx.exception.code, 2)
        finally:
            del os.environ["ROOM_HUNT_DENYLIST"]
            if saved is not None:
                os.environ["DENYLIST"] = saved


class Installer(unittest.TestCase):
    """M11: hooks land where git looks for them, and a foreign hook is never overwritten."""

    def run_installer(self, cwd):
        return subprocess.run(["sh", str(INSTALLER)], cwd=cwd, capture_output=True, text=True)

    def test_installs_all_three_hooks_in_a_linked_worktree(self):
        with tempfile.TemporaryDirectory() as d:
            main = Path(d) / "main"
            main.mkdir()
            git = make_repo(main)
            (main / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            git("worktree", "add", "-q", str(Path(d) / "wt"), "-b", "wt")
            result = self.run_installer(Path(d) / "wt")
            self.assertEqual(result.returncode, 0, result.stderr)
            hooks = main / ".git" / "hooks"
            for name in ("pre-commit", "commit-msg", "pre-push"):
                self.assertIn("guard/check_public.py", (hooks / name).read_text(), name)

    def test_refuses_to_replace_a_foreign_hook(self):
        with tempfile.TemporaryDirectory() as d:
            make_repo(d)
            hook = Path(d) / ".git" / "hooks" / "pre-commit"
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text("#!/bin/sh\necho mine\n")
            result = self.run_installer(d)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(hook.read_text(), "#!/bin/sh\necho mine\n")


if __name__ == "__main__":
    unittest.main()
