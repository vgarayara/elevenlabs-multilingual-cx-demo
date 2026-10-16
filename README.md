# ElevenLabs Multilingual CX Demo

One customer-service moment, voiced for five markets: **US English** and **Mexican, Colombian, Peruvian and Chilean Spanish**.

In contact-center AI, a voice that sounds local changes how customers feel about the conversation. They feel understood, not processed. This small prototype shows how quickly you can produce market-specific voices for the same agent script with the [ElevenLabs API](https://elevenlabs.io/docs), so a customer can hear the difference before committing to a deployment.

## What it does

`demo.py` reads one scenario (`scenarios.json`, an AI agent confirming a lost-card block and replacement) with a line written for each market. It uses local phrasing, such as *"con mucho gusto"* in Colombia and *"días útiles"* in Peru. It then generates one MP3 per market with the voice you choose for that market.

```
output/
├── card_replacement_en-US.mp3
├── card_replacement_es-MX.mp3
├── card_replacement_es-CO.mp3
├── card_replacement_es-PE.mp3
└── card_replacement_es-CL.mp3
```

## Quick start

Requires Python 3.9+ and an ElevenLabs API key. The free plan works with ElevenLabs’ built-in voices; local-accent voices from the Voice Library need a paid plan.

```bash
git clone https://github.com/vgarayara/elevenlabs-multilingual-cx-demo.git
cd elevenlabs-multilingual-cx-demo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # then paste your API key into .env
python demo.py --dry-run          # preview, no API calls
python demo.py --list-voices      # pick a voice for each market
cp voices.example.json voices.json  # paste the voice IDs
python demo.py                    # generate the MP3s into ./output
```

Generate only some markets with `python demo.py --locales en-US es-PE`.

## Tests

The tests mock the API, so they run without a key:

```bash
python -m unittest discover -s tests -v
```

## Adapting it

- **New scenario:** copy `scenarios.json`, change the lines and run `python demo.py --scenario my_scenario.json`.
- **New market:** add a locale to the scenario's `lines` and a voice to `voices.json`.
- **Different model:** `python demo.py --model eleven_turbo_v2_5` (default: `eleven_multilingual_v2`).

Your `.env`, `voices.json` and generated audio are git-ignored, so keys and outputs stay on your machine.

---

Built by [Victor Garayar](https://www.linkedin.com/in/vgarayar). I've led voice and agentic AI deployments in the US, Europe and Latin America.
