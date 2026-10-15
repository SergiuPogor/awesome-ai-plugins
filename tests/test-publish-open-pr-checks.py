import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "publish_open_pr_checks",
    Path(__file__).resolve().parents[1] / "scripts/publish-open-pr-checks.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PublishOpenPrChecksTests(unittest.TestCase):
    def test_failed_source_scan_blocks_merge(self):
        result = {"pr_number": 411, "state": "scan", "failure_reasons": []}
        conclusion, title, summary = MODULE.check_summary(
            result, {411: ["failure"]}
        )

        self.assertEqual(conclusion, "failure")
        self.assertEqual(title, "Centralized score not established")
        self.assertIn("score of at least 80", summary)
        self.assertIn("Finding severities are advisory", summary)
        self.assertIn("Keep the contribution blocked", summary)

    def test_unavailable_source_scan_blocks_merge(self):
        conclusion, title, summary = MODULE.check_summary(
            {"pr_number": 411, "state": "scan", "failure_reasons": []}, {}
        )

        self.assertEqual(conclusion, "failure")
        self.assertEqual(title, "Centralized score unavailable")
        self.assertIn("did not establish a score of at least 80", summary)

    def test_failed_scan_comment_is_one_paragraph_with_conditional_source_ci_guidance(self):
        result = {
            "pr_number": 411,
            "state": "scan",
            "author_login": "builder",
            "contributions": [
                {
                    "owner": "owner",
                    "repo": "plugin",
                    "scanner_ci": "not_detected",
                }
            ],
        }
        body = MODULE.remediation_comment(
            result,
            "failure",
            "Centralized score not established",
            "The centralized scan did not establish a score of at least 80.",
            "https://github.com/example/repo/actions/runs/1",
        )

        self.assertNotIn("\n", body)
        self.assertNotIn("\\n", body)
        self.assertIn("@builder, The centralized scan did not establish", body)
        self.assertIn("source-repository scanner CI is recommended, not required", body)
        self.assertIn("If the completed report confirms a score below 80", body)
        self.assertIn("reproduce locally", body)
        self.assertIn("link the source run", body)
        self.assertIn("request review", body)
        self.assertNotIn("Community Plugins format", body)

    def test_passing_score_does_not_recommend_source_scanner_ci(self):
        result = {
            "pr_number": 411,
            "state": "scan",
            "author_login": "builder",
            "contributions": [{"owner": "owner", "repo": "plugin", "scanner_ci": "not_detected"}],
        }
        body = MODULE.remediation_comment(
            result,
            "success",
            "Centralized score threshold passed",
            "The centralized scan met the score threshold of 80.",
            "https://github.com/example/repo/actions/runs/1",
        )

        self.assertNotIn("\n", body)
        self.assertNotIn("\\n", body)
        self.assertIn("score threshold of 80 was met", body)
        self.assertNotIn("scanner CI is recommended", body)
        self.assertNotIn("trust score", body)

    def test_catalog_failure_comment_is_one_paragraph_without_scanner_gate(self):
        result = {
            "pr_number": 411,
            "state": "failure",
            "author_login": "builder",
            "failure_reasons": ["entry is not alphabetical"],
        }
        body = MODULE.remediation_comment(
            result,
            "failure",
            "Contribution requirements failed",
            "Catalog validation failed: entry is not alphabetical",
            "https://github.com/example/repo/actions/runs/1",
        )

        self.assertNotIn("\n", body)
        self.assertIn("entry is not alphabetical", body)
        self.assertNotIn("scanner CI", body)


if __name__ == "__main__":
    unittest.main()
