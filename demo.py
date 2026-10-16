"""Voice one customer-service conversation in several markets with the ElevenLabs API.

Usage:
    python demo.py --dry-run          # show what would be generated (no API key needed)
    python demo.py --list-voices      # list the voices available in your account
    python demo.py                    # generate one MP3 per market into ./output
    python demo.py --locales en-US es-PE
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

API_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_multilingual_v2"
DEFAULT_FORMAT = "mp3_44100_128"
HERE = Path(__file__).resolve().parent


def load_dotenv(path: Path = HERE / ".env") -> None:
    """Read KEY=VALUE lines from a local .env file into the environment (if present)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_voice_map(path: Path) -> dict[str, str]:
    """Return {locale: voice_id}, ignoring comments and placeholders."""
    if not path.exists():
        return {}
    data = load_json(path)
    return {
        k: v
        for k, v in data.items()
        if not k.startswith("_") and isinstance(v, str) and v and not v.startswith("PASTE_")
    }


def list_voices(api_key: str) -> list[dict]:
    resp = requests.get(f"{API_BASE}/voices", headers={"xi-api-key": api_key}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("voices", [])


def synthesize(text: str, voice_id: str, api_key: str, model_id: str = DEFAULT_MODEL,
               output_format: str = DEFAULT_FORMAT) -> bytes:
    """Convert text to speech and return the audio bytes."""
    resp = requests.post(
        f"{API_BASE}/text-to-speech/{voice_id}",
        params={"output_format": output_format},
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        json={
            "text": text,
            "model_id": model_id,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs API error {resp.status_code}: {resp.text[:300]}")
    return resp.content


def plan(lines: dict[str, str], locales: list[str] | None, voice_map: dict[str, str],
         default_voice: str | None) -> list[tuple[str, str, str | None]]:
    """Return (locale, text, voice_id) for each line to generate."""
    selected = locales or list(lines)
    unknown = [loc for loc in selected if loc not in lines]
    if unknown:
        raise SystemExit(f"Unknown locale(s): {', '.join(unknown)}. Available: {', '.join(lines)}")
    return [(loc, lines[loc], voice_map.get(loc, default_voice)) for loc in selected]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", type=Path, default=HERE / "scenarios.json")
    parser.add_argument("--voices", type=Path, default=HERE / "voices.json",
                        help="JSON file mapping each locale to a voice_id")
    parser.add_argument("--locales", nargs="+", help="only generate these locales, e.g. en-US es-MX")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", type=Path, default=HERE / "output")
    parser.add_argument("--list-voices", action="store_true", help="list voices in your account and exit")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without calling the API")
    args = parser.parse_args(argv)

    load_dotenv()
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()

    if not args.dry_run and not api_key:
        print("Missing ELEVENLABS_API_KEY. Add it to a .env file (see .env.example) or export it.",
              file=sys.stderr)
        return 1

    if args.list_voices:
        for v in list_voices(api_key):
            labels = v.get("labels") or {}
            extra = ", ".join(f"{k}={labels[k]}" for k in ("accent", "language", "gender") if labels.get(k))
            print(f"{v['voice_id']}  {v.get('name', '')}  [{v.get('category', '')}]  {extra}")
        return 0

    scenario = load_json(args.scenario)
    voice_map = load_voice_map(args.voices)
    default_voice = os.environ.get("ELEVENLABS_DEFAULT_VOICE_ID") or None

    if not args.dry_run and not voice_map and not default_voice:
        voices = list_voices(api_key)
        if not voices:
            print("No voices found in your account.", file=sys.stderr)
            return 1
        default_voice = voices[0]["voice_id"]
        print(f"No voices.json found; using '{voices[0].get('name')}' for every locale.")

    jobs = plan(scenario["lines"], args.locales, voice_map, default_voice)

    print(f"Scenario: {scenario.get('scenario')} — {scenario.get('description', '')}")
    if args.dry_run:
        for loc, text, voice in jobs:
            print(f"[dry-run] {loc} (voice: {voice or 'auto'}): {text}")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    for loc, text, voice in jobs:
        audio = synthesize(text, voice, api_key, model_id=args.model)
        path = args.out / f"{scenario.get('scenario', 'demo')}_{loc}.mp3"
        path.write_bytes(audio)
        print(f"✓ {loc}: {path} ({len(audio) // 1024} KB)")
    print("Done. Open the MP3 files to compare the voices.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
