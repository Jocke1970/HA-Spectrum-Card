# HA-Spectrum-Card

**Development prototype — not yet a beta release.** A real 10-band LED spectrum for Home Assistant, based on an external FFT analyzer. First target: Radio Browser streamed to Google Home Mini through `media_player.kok`.

## Features
- Classic 31, 62, 125, 250, 500, 1k, 2k, 4k, 8k and 16k Hz LED layout
- Real FFT data only; never simulated or random bars
- Read-only monitoring: no commands sent to Chromecast/Spotify
- Simple Lovelace visual editor
- Explicit standby / unsupported Spotify / waiting-for-FFT states

## How it works

Home Assistant player → analyzer polls HA REST API → FFmpeg independently reads an HTTP(S) radio stream → NumPy FFT → MQTT discovery → Home Assistant sensor → JavaScript Lovelace card.

**Important:** Spotify playing on Google Home Mini does not expose raw audio through the HA player. It can be detected, but **not** FFT-analyzed by this prototype. Radio Browser exposes a URL in `media_content_id`. A parallel fetch may not be perfectly synchronized with the speaker and may not be allowed by every station.

## Installation (development testing, not production)

Requires FFmpeg, Python 3, a reachable MQTT broker and Home Assistant MQTT integration. The analyzer runs outside HA Core, such as on Linux Mint or a separate host.

1. Set up an MQTT broker and HA MQTT integration.
2. On a Linux host run `sudo apt install ffmpeg python3-venv`.
3. Clone/check out **dev**, create a venv and install dependencies: `python3 -m venv .venv && .venv/bin/pip install -r analyzer/requirements.txt`.
4. Export `HA_URL`, `HA_TOKEN`, `MEDIA_ENTITY`, `MQTT_HOST`, `MQTT_USER`, `MQTT_PASSWORD` according to `analyzer/.env.example`. **Never commit tokens or passwords.**
5. Run `.venv/bin/python analyzer/analyzer.py` while Radio Browser is playing on `media_player.kok`. Check whether MQTT discovers `sensor.ha_spectrum_levels`.
6. Copy `dist/ha-spectrum-card.js` to `/config/www/ha-spectrum-card.js`. Add `/local/ha-spectrum-card.js` as a JavaScript module under Dashboard resources, then add `examples/lovelace.yaml` as a custom card.

## Limitations and testing needed

- Not tested live on user's Home Assistant / Google Home Mini; no beta or stable release.
- Requires separate running Python + FFmpeg analyzer, and MQTT.
- Separate stream decoding causes delay and possible desynchronization.
- Polling and blocking/stream recovery behavior need soak testing.
- Frequency mapping and level scaling need calibration on real radio content.
- No peak hold yet; implement after live levels are verified.
- Prototype targets one player; multiroom requires distinct MQTT topics and discovery IDs.
- Treat radio URLs as untrusted input: for deployment, restrict permitted remote hosts and protect the analyzer host/network.
- Status and data freshness are checked by the card; the analyzer does not control player volume or transport.

## Development policy

`dev → beta → main`. The **dev** branch contains experimental code only. Do not install dev on production Home Assistant. Promote to beta only after validating the analyzer and frontend, then to main after stable real-world testing.
