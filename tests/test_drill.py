"""Behavior and publication-surface checks; no third-party packages or network."""
from collections import Counter
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("drill", ROOT / "drill.py")
drill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drill)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.links = []
        self.ids = []
        self.tags = []
        self.external_assets = []
        self.canonicals = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags.append(tag)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))
        if tag in ("script", "img", "iframe") or (tag == "link" and attrs.get("rel") != "canonical"):
            url = attrs.get("src", attrs.get("href", ""))
            if url.startswith(("http:", "https:", "//")):
                self.external_assets.append(url)

    def handle_data(self, data):
        self.text.append(data)


class PracticeTests(unittest.TestCase):
    def run_cli(self, *args, cwd=ROOT):
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "drill.py"), *args],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=10,
        )

    def test_dataset_has_twenty_distinct_balanced_cards(self):
        cards = drill.load_cards()
        self.assertEqual(len(cards), 20)
        self.assertEqual(len({card["id"] for card in cards}), 20)
        self.assertEqual(len({card["prompt"] for card in cards}), 20)
        self.assertEqual(Counter(card["role"] for card in cards),
                         Counter({role: 4 for role in drill.ROLES}))
        for card in cards:
            self.assertEqual(set(card), drill.FIELDS)
            self.assertEqual(len(card["followups"]), 3)
            self.assertEqual(len(set(card["followups"])), 3)
            self.assertTrue(all(question.endswith("?") for question in card["followups"]))
            self.assertTrue(card["evidence_check"].strip())
            self.assertTrue(card["common_pitfall"].strip())

    def test_every_role_runs_a_complete_ten_minute_session(self):
        for role in drill.ROLES:
            with self.subTest(role=role):
                result = self.run_cli("--role", role, "--seed", "17")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("00:00-01:00", result.stdout)
                self.assertIn("09:00-10:00", result.stdout)
                self.assertIn("not validated employer interview questions", result.stdout)
                selected = next(card for card in drill.load_cards()
                                if "Card: " + card["id"] + "\n" in result.stdout)
                self.assertEqual(selected["role"], role)
                for text in [selected["prompt"], *selected["followups"],
                             selected["evidence_check"], selected["common_pitfall"]]:
                    self.assertIn(text, result.stdout)
        self.assertEqual(sum(step[2] for step in drill.SCHEDULE), 600)

    def test_seed_is_repeatable_across_processes_and_working_directories(self):
        first = self.run_cli("--role", "designer", "--seed", "-3")
        with tempfile.TemporaryDirectory(prefix=".test-", dir=ROOT) as folder:
            second = self.run_cli("--role", "designer", "--seed", "-3", cwd=folder)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_seeds_can_reach_every_card_within_each_role(self):
        cards = drill.load_cards()
        for role in drill.ROLES:
            reached = {drill.choose_card(cards, role, seed)["id"] for seed in range(64)}
            expected = {card["id"] for card in cards if card["role"] == role}
            self.assertEqual(reached, expected)

    def test_export_is_exact_utf8_stdout_at_explicit_path(self):
        with tempfile.TemporaryDirectory(prefix=".test-", dir=ROOT) as folder:
            target = Path(folder) / "my practice.md"
            result = self.run_cli("--role", "data-analyst", "--seed", "42",
                                  "--export", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), result.stdout)
            self.assertEqual(list(Path(folder).iterdir()), [target])
            self.assertIn("Saved Markdown to", result.stderr)

    def test_relative_export_uses_working_directory(self):
        with tempfile.TemporaryDirectory(prefix=".test-", dir=ROOT) as folder:
            result = self.run_cli("--role", "customer-success", "--seed", "42",
                                  "--export", "session.md", cwd=folder)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((Path(folder) / "session.md").read_text(encoding="utf-8"),
                             result.stdout)

    def test_existing_export_is_never_overwritten(self):
        with tempfile.TemporaryDirectory(prefix=".test-", dir=ROOT) as folder:
            target = Path(folder) / "notes.md"
            target.write_bytes(b"private notes remain")
            result = self.run_cli("--role", "product-manager", "--seed", "1",
                                  "--export", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_bytes(), b"private notes remain")
            self.assertEqual(result.stdout, "")

    def test_unsupported_role_is_rejected_before_export(self):
        with tempfile.TemporaryDirectory(prefix=".test-", dir=ROOT) as folder:
            result = self.run_cli("--role", "astronaut", "--seed", "1",
                                  "--export", str(Path(folder) / "no.md"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid choice", result.stderr)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_non_integer_seed_is_rejected(self):
        result = self.run_cli("--role", "designer", "--seed", "1.5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid int value", result.stderr)

    def test_missing_export_parent_is_not_created(self):
        with tempfile.TemporaryDirectory(prefix=".test-", dir=ROOT) as folder:
            target = Path(folder) / "absent" / "notes.md"
            result = self.run_cli("--role", "designer", "--seed", "1",
                                  "--export", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.parent.exists())

    def test_html_contains_complete_cards_and_working_internal_anchors(self):
        page = Page()
        page.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        text = " ".join(page.text)
        for card in drill.load_cards():
            self.assertIn(card["id"], page.ids)
            for item in [card["prompt"], *card["followups"],
                         card["evidence_check"], card["common_pitfall"]]:
                self.assertIn(item, text)
        self.assertEqual(len(page.ids), len(set(page.ids)))
        for link in page.links:
            href = link.get("href", "")
            if href.startswith("#"):
                self.assertIn(href[1:], page.ids)
            elif not href.startswith(("http:", "https:")):
                self.assertTrue((ROOT / href).is_file(), href)

    def test_public_page_has_one_contextual_followed_link_and_no_active_collection(self):
        page = Page()
        page.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        target = "https://makeinterview.com/en/blog/mianshi-zhuishao-yuanxing"
        matches = [link for link in page.links if link.get("href") == target]
        self.assertEqual(len(matches), 1)
        self.assertFalse({"nofollow", "ugc", "sponsored"} &
                         set(matches[0].get("rel", "").lower().split()))
        self.assertFalse({"script", "form", "iframe", "input"} & set(page.tags))
        self.assertEqual(page.external_assets, [])
        self.assertEqual(page.canonicals, ["https://szj2ys.github.io/interview-evidence-cards/"])
        self.assertIn("team behind MockLive / MakeInterview", " ".join(page.text))

    def test_help_documents_all_roles_and_export(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        for role in drill.ROLES:
            self.assertIn(role, result.stdout)
        self.assertIn("--export", result.stdout)


if __name__ == "__main__":
    unittest.main()
