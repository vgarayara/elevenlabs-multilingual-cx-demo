"""Unit tests that run without an API key (the ElevenLabs API is mocked)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import demo  # noqa: E402


class DemoTests(unittest.TestCase):
    def test_scenario_has_all_markets(self):
        lines = demo.load_json(demo.HERE / "scenarios.json")["lines"]
        self.assertEqual(set(lines), {"en-US", "es-MX", "es-CO", "es-PE", "es-CL"})
        self.assertTrue(all(text.strip() for text in lines.values()))

    def test_voice_map_ignores_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "voices.json"
            path.write_text(json.dumps({"_comment": "x", "en-US": "abc123", "es-MX": "PASTE_VOICE_ID_HERE"}))
            self.assertEqual(demo.load_voice_map(path), {"en-US": "abc123"})

    def test_plan_uses_default_voice_when_missing(self):
        jobs = demo.plan({"en-US": "hi", "es-PE": "hola"}, None, {"en-US": "v1"}, "fallback")
        self.assertEqual(jobs, [("en-US", "hi", "v1"), ("es-PE", "hola", "fallback")])

    def test_plan_rejects_unknown_locale(self):
        with self.assertRaises(SystemExit):
            demo.plan({"en-US": "hi"}, ["fr-FR"], {}, None)

    def test_dry_run_needs_no_api_key(self):
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(demo, "load_dotenv"):
            self.assertEqual(demo.main(["--dry-run"]), 0)

    def test_generate_writes_mp3_files(self):
        fake = mock.Mock(status_code=200, content=b"ID3fake-audio")
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test"}, clear=True), \
                mock.patch.object(demo, "load_dotenv"), \
                mock.patch.object(demo.requests, "post", return_value=fake) as post:
            voices = Path(tmp) / "voices.json"
            voices.write_text(json.dumps({"en-US": "v1", "es-CO": "v2"}))
            code = demo.main(["--voices", str(voices), "--locales", "en-US", "es-CO", "--out", tmp])
            self.assertEqual(code, 0)
            self.assertEqual(post.call_count, 2)
            self.assertTrue((Path(tmp) / "card_replacement_en-US.mp3").exists())
            self.assertTrue((Path(tmp) / "card_replacement_es-CO.mp3").exists())
            self.assertIn("/text-to-speech/v1", post.call_args_list[0].args[0])


if __name__ == "__main__":
    unittest.main()
