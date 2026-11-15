# Spectrum FFT experimental app (dev only)

This app reads Home Assistant media player state through the Supervisor's Core API, independently decodes the **public HTTP(S) radio stream** using FFmpeg and publishes FFT results to an existing MQTT broker. It never controls a media player.

**Do not install from dev in a production system.** This is packaging scaffolding for controlled verification; no image build or HA OS test has passed yet.

Requires Home Assistant OS (not Home Assistant Container), MQTT integration and broker. The default broker host `core-mosquitto` assumes the official Mosquitto broker app is installed. Supply its username/password in app options. If your MQTT integration uses another broker, adjust the host.

A custom app repository needs the root `repository.yaml`. Docker builds and the path layout must be validated before a beta release. The Dockerfile uses only files from this app directory. Verify the build in Home Assistant before publishing. Do not expose this app publicly until URL restrictions and recovery logic have been reviewed.

App is manual-start for test isolation. Stop it to end FFT processing.
