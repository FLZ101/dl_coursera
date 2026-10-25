import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from dl_coursera.Downloader import (
    DownloaderBuiltin,
    DownloaderCurl,
    DownloaderAria2,
    DownloaderUget,
    DownloaderAria2_rpc,
)


class TestSkipExistingFiles(unittest.TestCase):
    """Test that downloaders skip files that already exist."""

    def _make_ts(self):
        ts = MagicMock()
        ts.register_task.return_value.side_effect = lambda func: func
        return ts

    def test_builtin_skips_existing_file(self):
        """DownloaderBuiltin should not download if file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'existing.mp4')
            with open(filename, 'wb') as f:
                f.write(b'original content')

            ts = self._make_ts()
            dl = DownloaderBuiltin(
                dl_tasks=[{'url': 'http://example.com/video.mp4', 'filename': filename}],
                ts=ts,
            )
            dl.download()

            with open(filename, 'rb') as f:
                content = f.read()
            self.assertEqual(content, b'original content')

    def test_curl_skips_existing_file(self):
        """DownloaderCurl should not invoke curl if file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'existing.mp4')
            with open(filename, 'wb') as f:
                f.write(b'original')

            ts = self._make_ts()
            with patch.object(DownloaderCurl, 'check', return_value=None):
                dl = DownloaderCurl(
                    dl_tasks=[{'url': 'http://example.com/video.mp4', 'filename': filename}],
                    ts=ts,
                )
                with patch('dl_coursera.Downloader.subprocess.run') as mock_run:
                    dl.download()
                    mock_run.assert_not_called()

    def test_aria2_skips_existing_file(self):
        """DownloaderAria2 should not invoke aria2c if file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'existing.mp4')
            with open(filename, 'wb') as f:
                f.write(b'original')

            ts = self._make_ts()
            with patch.object(DownloaderAria2, 'check', return_value=None):
                dl = DownloaderAria2(
                    dl_tasks=[{'url': 'http://example.com/video.mp4', 'filename': filename}],
                    ts=ts,
                )
                with patch('dl_coursera.Downloader.subprocess.run') as mock_run:
                    dl.download()
                    mock_run.assert_not_called()

    def test_uget_skips_existing_file(self):
        """DownloaderUget should not add task if file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'existing.mp4')
            with open(filename, 'wb') as f:
                f.write(b'original')

            with patch.object(DownloaderUget, 'check', return_value=None):
                dl = DownloaderUget(
                    dl_tasks=[{'url': 'http://example.com/video.mp4', 'filename': filename}]
                )
                with patch('dl_coursera.Downloader.subprocess.run') as mock_run:
                    dl.download()
                    mock_run.assert_not_called()

    def test_aria2_rpc_skips_existing_file(self):
        """DownloaderAria2_rpc should not add URI if file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'existing.mp4')
            with open(filename, 'wb') as f:
                f.write(b'original')

            mock_client = MagicMock()
            dl = DownloaderAria2_rpc(
                dl_tasks=[{'url': 'http://example.com/video.mp4', 'filename': filename}],
                url='http://localhost:6800/rpc',
            )
            dl._client = mock_client
            dl.download()
            mock_client.aria2.addUri.assert_not_called()


if __name__ == '__main__':
    unittest.main()
