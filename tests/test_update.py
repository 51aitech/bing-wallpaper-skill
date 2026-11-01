import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('updater', Path(__file__).parents[1] / 'scripts/update.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'state'
        self.pictures = Path(self.temp.name) / 'photos'
        self.root.mkdir()
        self.pictures.mkdir()
        self.enterContext(patch.object(updater, 'root', self.root))
        self.enterContext(patch.object(updater, 'pictures', self.pictures))
        self.enterContext(patch('sys.argv', ['update.py']))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))

    def test_same_day_skips_network_and_native_calls(self):
        image = self.pictures / 'existing.jpg'
        image.write_bytes(b'photo')
        state = {'checked_on': updater.datetime.now().strftime('%Y-%m-%d'), 'file': str(image)}
        (self.root / 'current.json').write_text(json.dumps(state))
        with patch.object(updater, 'fetch') as fetch, patch.object(updater.subprocess, 'check_output') as native:
            with self.assertRaises(SystemExit) as exit:
                updater.main()
            self.assertEqual(exit.exception.code, 0)
            fetch.assert_not_called()
            native.assert_not_called()

    def test_success_preserves_attribution_after_verification(self):
        metadata = {'wp': True, 'urlbase': '/th?id=OHR.Example_EN-US123', 'copyright': 'Example photographer'}
        target = self.pictures / 'OHR.Example_EN-US123_UHD.jpg'
        with patch.object(updater, 'fetch', side_effect=[json.dumps({'images': [metadata]}).encode(), b'\xff\xd8\xff' + b'x' * 10000]), patch.object(updater.subprocess, 'check_output', side_effect=['Applied', json.dumps([str(target)])]):
            updater.main()
        state = json.loads((self.root / 'current.json').read_text())
        self.assertEqual(state['image']['copyright'], metadata['copyright'])
        self.assertEqual(state['file'], str(target))

    def test_download_failure_retains_old_state(self):
        previous = '{"checked_on":"old","file":"old.jpg"}'
        (self.root / 'current.json').write_text(previous)
        with patch.object(updater, 'fetch', side_effect=RuntimeError('Offline')), patch.object(updater.subprocess, 'check_output') as native:
            with self.assertRaises(SystemExit) as exit:
                updater.main()
            self.assertEqual(exit.exception.code, 1)
            native.assert_not_called()
        self.assertEqual((self.root / 'current.json').read_text(), previous)

    def test_untrusted_identifier_is_rejected(self):
        metadata = {'wp': True, 'urlbase': '/th?id=OHR../../outside'}
        with patch.object(updater, 'fetch', return_value=json.dumps({'images': [metadata]}).encode()), patch.object(updater.subprocess, 'check_output') as native:
            with self.assertRaises(SystemExit):
                updater.main()
            native.assert_not_called()
        self.assertFalse((self.root / 'current.json').exists())

    def test_proxy_is_preserved_in_fetch(self):
        with patch.dict(os.environ, {'HTTPS_PROXY': 'http://proxy.invalid:8080'}, clear=True), patch.object(updater.subprocess, 'check_output', return_value=b'{}') as command:
            updater.fetch('https://www.bing.com/example')
        args = command.call_args.args[0]
        self.assertEqual(args[args.index('--proxy') + 1], 'http://proxy.invalid:8080')
        self.assertEqual(args[args.index('--noproxy') + 1], '')


if __name__ == '__main__':
    unittest.main()
