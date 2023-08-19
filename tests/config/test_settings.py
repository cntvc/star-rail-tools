import json
import os
import shutil
import tempfile
import unittest

from star_rail.config.settings import Settings


class TestSettingsModule(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "settings.json")
        self.mock_config = {
            "FLAG_AUTO_UPDATE": False,
            "UPDATE_SOURCE": "Coding",
            "OLD_EXE_NAME": "old.exe",
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_config_initialization(self):
        settings = Settings(self.config_path)
        self.assertTrue(settings.FLAG_AUTO_UPDATE)
        self.assertFalse(settings.FLAG_UPDATED_COMPLETE)
        self.assertEqual(settings.UPDATE_SOURCE, "Github")

    def test_save_config(self):
        settings = Settings(self.config_path)
        settings.update_config(self.mock_config)
        settings.save_config()

        with open(self.config_path, "r") as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config["FLAG_AUTO_UPDATE"], self.mock_config["FLAG_AUTO_UPDATE"])
        self.assertEqual(saved_config["UPDATE_SOURCE"], self.mock_config["UPDATE_SOURCE"])

    def test_update_config(self):
        settings = Settings(self.config_path)
        settings.update_config(self.mock_config)

        self.assertEqual(settings.FLAG_AUTO_UPDATE, self.mock_config["FLAG_AUTO_UPDATE"])
        self.assertEqual(settings.UPDATE_SOURCE, self.mock_config["UPDATE_SOURCE"])

    def test_refresh_config(self):
        settings = Settings(self.config_path)
        with open(self.config_path, "w") as f:
            json.dump(self.mock_config, f)

        settings.refresh_config(self.config_path)

        self.assertEqual(settings.FLAG_AUTO_UPDATE, self.mock_config["FLAG_AUTO_UPDATE"])
        self.assertEqual(settings.UPDATE_SOURCE, self.mock_config["UPDATE_SOURCE"])
