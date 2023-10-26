import unittest
from unittest.mock import Mock, patch

from star_rail.module.updater import CodingUpdater, GithubUpdater


class TestGithubUpdater(unittest.TestCase):
    def setUp(self):
        self.updater = GithubUpdater()

    @patch("star_rail.module.updater.app_version", "1.0.2")
    def test_check_update_true(self):
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "tag_name": "2.0.0",
                "assets": [
                    {
                        "browser_download_url": "https://example.com/download",
                        "name": "test_2.0.1.exe",
                    }
                ],
            }
            mock_get.return_value = mock_response
            result, update_context = self.updater.check_update()
            self.assertTrue(result)
            self.assertEqual(update_context.version, "2.0.0")
            self.assertEqual(update_context.download_url, "https://example.com/download")

    @patch("star_rail.module.updater.app_version", "2.0.2")
    def test_check_update_false(self):
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "tag_name": "2.0.0",
                "assets": [
                    {
                        "browser_download_url": "https://example.com/download",
                        "name": "test_2.0.1.exe",
                    }
                ],
            }
            mock_get.return_value = mock_response
            result, update_context = self.updater.check_update()
            self.assertFalse(result)
            self.assertIsNone(update_context)


class TestCodingUpdater(unittest.TestCase):
    def setUp(self):
        self.updater = CodingUpdater()

    @patch("star_rail.module.updater.app_version", "1.0.2")
    def test_check_update(self):
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": {
                    "list": [
                        {
                            "latestVersionName": "2.0",
                            "name": "artifact.exe",
                            "registryUrl": "https://example.com/registry",
                            "projectName": "project",
                            "repoName": "repo",
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response
            result, update_context = self.updater.check_update()
            self.assertTrue(result)
            self.assertEqual(update_context.version, "2.0")
            self.assertEqual(update_context.name, "artifact_2.0.exe")
            self.assertEqual(
                update_context.download_url,
                "https://example.com/registry/project/repo/artifact.exe?version=2.0",
            )
