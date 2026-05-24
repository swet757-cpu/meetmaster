import os
from pathlib import Path
import tempfile
import unittest

from app.config.settings import _load_env_file, load_settings


class SettingsTest(unittest.TestCase):
    def test_load_env_file_without_overriding_existing_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "BOT_TOKEN=from_file\nADMIN_TELEGRAM_IDS=111\n",
                encoding="utf-8",
            )

            previous = os.environ.get("BOT_TOKEN")
            previous_admin_ids = os.environ.get("ADMIN_TELEGRAM_IDS")
            os.environ["BOT_TOKEN"] = "from_environment"
            os.environ.pop("ADMIN_TELEGRAM_IDS", None)
            try:
                _load_env_file(env_path)
                self.assertEqual(os.environ["BOT_TOKEN"], "from_environment")
                self.assertEqual(os.environ["ADMIN_TELEGRAM_IDS"], "111")
            finally:
                if previous is None:
                    os.environ.pop("BOT_TOKEN", None)
                else:
                    os.environ["BOT_TOKEN"] = previous
                if previous_admin_ids is None:
                    os.environ.pop("ADMIN_TELEGRAM_IDS", None)
                else:
                    os.environ["ADMIN_TELEGRAM_IDS"] = previous_admin_ids

    def test_google_calendar_enabled_flag(self) -> None:
        previous = os.environ.get("GOOGLE_CALENDAR_ENABLED")
        try:
            os.environ["GOOGLE_CALENDAR_ENABLED"] = "true"
            settings = load_settings()
            self.assertTrue(settings.google_calendar_enabled)
        finally:
            if previous is None:
                os.environ.pop("GOOGLE_CALENDAR_ENABLED", None)
            else:
                os.environ["GOOGLE_CALENDAR_ENABLED"] = previous


if __name__ == "__main__":
    unittest.main()
