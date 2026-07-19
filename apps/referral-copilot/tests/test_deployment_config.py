from pathlib import Path
import unittest


APP_DIR = Path(__file__).resolve().parents[1]


class DeploymentConfigTests(unittest.TestCase):
    def test_streamlit_uses_databricks_managed_host_and_port(self) -> None:
        config = (APP_DIR / "app.yaml").read_text(encoding="utf-8")

        self.assertIn("command: ['streamlit', 'run', 'app.py']", config)
        self.assertNotIn("--server.port", config)
        self.assertNotIn("--server.address", config)


if __name__ == "__main__":
    unittest.main()
