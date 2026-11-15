"""Home Assistant OS app launcher; never logs credentials."""
import json
import os
from pathlib import Path
import runpy

opts=json.loads(Path("/data/options.json").read_text())
token=os.environ.get("SUPERVISOR_TOKEN")
if not token:
    raise RuntimeError("Missing SUPERVISOR_TOKEN; Home Assistant API access unavailable")
os.environ["HA_URL"]="http://supervisor/core"
os.environ["HA_TOKEN"]=token
os.environ["MEDIA_ENTITY"]=opts.get("media_entity","media_player.kok")
os.environ["MQTT_HOST"]=opts.get("mqtt_host","core-mosquitto")
os.environ["MQTT_PORT"]=str(opts.get("mqtt_port",1883))
os.environ["MQTT_USER"]=opts.get("mqtt_user","")
os.environ["MQTT_PASSWORD"]=opts.get("mqtt_password","")
runpy.run_path("/opt/spectrum/analyzer.py",run_name="__main__")
