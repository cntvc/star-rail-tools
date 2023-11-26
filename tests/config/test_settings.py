import json
import os
import shutil
import tempfile
import unittest

from star_rail.config.settings import Settings


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_settings.json")
        self.default_config = {"CHECK_UPDATE": False, "DEFAULT_UID": "123456789"}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_default_settings(self):
        settings = Settings(config_path=self.config_path)

        self.assertTrue(settings.CHECK_UPDATE)
        self.assertEqual(settings.DEFAULT_UID, "")
        self.assertEqual(settings.ENCRYPT_KEY, "")
        self.assertEqual(settings.LANGUAGE, "")
        self.assertFalse(settings.DISPLAY_STARTER_WARP)

    def test_save_config(self):
        settings = Settings(config_path=self.config_path)

        settings.CHECK_UPDATE = False
        settings.DEFAULT_UID = "test_uid"
        settings.ENCRYPT_KEY = "test_salt"
        settings.save_config()

        with open(self.config_path, "r") as config:
            data = json.load(config)
        self.assertFalse(data["CHECK_UPDATE"])
        self.assertEqual(data["DEFAULT_UID"], "test_uid")
        self.assertEqual(data["ENCRYPT_KEY"], "test_salt")

    def test_refresh_config(self):
        self.assertFalse(os.path.exists(self.config_path))
        settings = Settings(self.config_path)

        with open(self.config_path, "w") as f:
            json.dump(self.default_config, f, ensure_ascii=False, sort_keys=False, indent=4)

        settings.refresh_config(self.config_path)

        self.assertFalse(settings.CHECK_UPDATE)
        self.assertEqual(settings.DEFAULT_UID, "123456789")
        self.assertEqual(settings.LANGUAGE, "")

    def test_update_config(self):
        settings = Settings(config_path=self.config_path)

        new_config_data = {"CHECK_UPDATE": True, "DEFAULT_UID": "test_uid", "TEST_ITEM": "NULL"}

        settings.update_config(new_config_data)

        self.assertTrue(settings.CHECK_UPDATE)
        self.assertEqual(settings.DEFAULT_UID, "test_uid")
        self.assertEqual(settings.ENCRYPT_KEY, "")
        self.assertEqual(settings.LANGUAGE, "")
        self.assertFalse(settings.DISPLAY_STARTER_WARP)
        self.assertFalse(hasattr(settings, "TEST_ITEM"))
