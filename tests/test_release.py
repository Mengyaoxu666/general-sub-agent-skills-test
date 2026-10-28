import importlib.util
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release", ROOT / "scripts/check_public_release.py")
RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE)


class ReleaseTests(unittest.TestCase):
    def test_release_matches_allowlist_and_privacy_rules(self):
        self.assertEqual(RELEASE.inspect()["problems"], [])

    def test_skill_contract(self):
        content = (ROOT / "skills/cost-aware-delegation/SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\nname: cost-aware-delegation\n"))
        self.assertLess(len(content), 1500)
        for phrase in ("降低主模型累计 Token", "general 默认承担", "每个任务完成即回报主模型",
                       "主模型逐任务验收", "重要失败项完整列出", "不重复读取全文", "通常最多两个"):
            self.assertIn(phrase, content)

    def test_command_does_not_override_model_or_agent(self):
        content = (ROOT / "commands/dispatch.md").read_text(encoding="utf-8")
        meta = content.split("---", 2)[1]
        self.assertIn("subagent: false", meta)
        self.assertNotRegex(meta, r"(?m)^(?:agent|model|subtask):")
        self.assertIn("$ARGUMENTS", content)
        self.assertIn("`cost-aware-delegation`", content)
        self.assertNotIn("!`", content)

    def test_document_links_resolve(self):
        for path in ROOT.rglob("*.md"):
            if ".git" in path.relative_to(ROOT).parts:
                continue
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://")):
                    self.assertTrue(RELEASE.allowed_url(target))
                else:
                    self.assertTrue((path.parent / target.split("#", 1)[0]).exists(), target)

    def test_scanner_recognizes_synthetic_secret_without_echoing(self):
        candidate = "gh" + "p_" + "X" * 36
        findings = RELEASE.scan_text(candidate)
        self.assertTrue(any(f["rule"] == "typical-secret" for f in findings))
        self.assertNotIn(candidate, json.dumps(findings))

    def test_scanner_rejects_personal_paths_and_network_addresses(self):
        samples = ("Z" + ":/" + "private-folder/file", "/" + "home/" + "sample/file",
                   ".".join(["192", "0", "2", "1"]), "someone" + "@" + "sample.invalid")
        for candidate in samples:
            self.assertTrue(RELEASE.scan_text(candidate))

    def test_scanner_rejects_unapproved_urls(self):
        candidate = "https" + "://" + "sample.invalid/resource"
        self.assertTrue(RELEASE.scan_text(candidate))
        self.assertFalse(RELEASE.allowed_url("https://opencode.ai/v2/docs/skills?" + "value=private"))

    def test_scanner_handles_markdown_link_punctuation(self):
        text = "[公开上游](https://github.com/obra/superpowers)，仅为公开来源。"
        self.assertEqual(RELEASE.scan_text(text), [])

    def test_manifest_paths_are_relative(self):
        for candidate in ("../private", "/outside", "folder\\file"):
            self.assertFalse(RELEASE.valid_release_path(candidate))


if __name__ == "__main__":
    unittest.main()
