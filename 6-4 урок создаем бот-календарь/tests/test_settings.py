import os
from pathlib import Path
import tempfile
import unittest

from app.config.settings import _load_env_file


class SettingsTest(unittest.TestCase):
    def test_load_env_file_without_overriding_existing_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "BOT_TOKEN=from_file\nADMIN_TELEGRAM_IDS=111\n",
                encoding="utf-8",
            )

            previous = os.environ.get("BOT_TOKEN")
            os.environ["BOT_TOKEN"] = "from_environment"
            try:
                _load_env_file(env_path)
                self.assertEqual(os.environ["BOT_TOKEN"], "from_environment")
                self.assertEqual(os.environ["ADMIN_TELEGRAM_IDS"], "111")
            finally:
                if previous is None:
                    os.environ.pop("BOT_TOKEN", None)
                else:
                    os.environ["BOT_TOKEN"] = previous
                os.environ.pop("ADMIN_TELEGRAM_IDS", None)


if __name__ == "__main__":
    unittest.main()

