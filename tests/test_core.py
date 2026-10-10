import tempfile
import unittest
from pathlib import Path

from scanner.cli import main
from scanner.policy import normalize_target, require_scope


class ScannerTests(unittest.TestCase):
    def test_hostname_normalization(self):
        self.assertEqual(
            normalize_target("LAB.EXAMPLE.TEST."),
            "lab.example.test",
        )

    def test_invalid_target(self):
        for target in (
            "",
            "https://example.test",
            "*.example.test",
            "10.0.0.0/24",
            "127.0.0.1;id",
        ):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    normalize_target(target)

    def test_scope_enforcement(self):
        with self.assertRaises(ValueError):
            require_scope("outside.test", ["lab.test"])

    def test_cli_workflow(self):
        with tempfile.TemporaryDirectory() as folder:
            main(["--workspace", folder, "init"])
            main([
                "--workspace",
                folder,
                "scope",
                "add",
                "lab.example.test",
            ])
            main([
                "--workspace",
                folder,
                "plan",
                "--profile",
                "web",
            ])
            main([
                "--workspace",
                folder,
                "run",
                "--dry-run",
            ])
            main([
                "--workspace",
                folder,
                "report",
                "--format",
                "markdown",
            ])

            self.assertTrue(
                (Path(folder) / "report.md").exists()
            )


if __name__ == "__main__":
    unittest.main()
