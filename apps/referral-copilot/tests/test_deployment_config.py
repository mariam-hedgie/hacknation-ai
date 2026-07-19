from pathlib import Path
import unittest


APP_DIR = Path(__file__).resolve().parents[1]


class DeploymentConfigTests(unittest.TestCase):
    def test_react_api_host_uses_managed_resources(self) -> None:
        config = (APP_DIR / "app.yaml").read_text(encoding="utf-8")
        runner = (APP_DIR / "run_app.py").read_text(encoding="utf-8")
        package = (APP_DIR / "package.json").read_text(encoding="utf-8")

        self.assertIn("command: ['python', 'run_app.py']", config)
        self.assertIn("valueFrom: postgres", config)
        self.assertIn("valueFrom: identity-pepper", config)
        self.assertIn("value: 'aven-facility-search'", config)
        self.assertIn("valueFrom: facility-evidence-index", config)
        self.assertIn('os.getenv("DATABRICKS_APP_PORT"', runner)
        self.assertIn('"build": "npm --workspace frontend run build"', package)


if __name__ == "__main__":
    unittest.main()
