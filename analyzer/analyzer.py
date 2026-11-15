"""Read-only Radio Browser FFT analyzer; requires FFmpeg, HA REST and MQTT."""
import json, logging, os, subprocess, time, select
from datetime import datetime, timezone
from urllib.parse import urlparse
import numpy as np
import requests
import paho.mqtt.client as mqtt

HA_URL=os.environ["HA_URL"].rstrip("/")
HA_TOKEN=os.environ["HA_TOKEN"]
ENTITY=os.getenv("MEDIA_ENTITY","media_player.kok")
HOST=os.getenv("MQTT_HOST","localhost")
PORT=int(os.getenv("MQTT_PORT","1883"))
SAMPLE_RATE=44100
FFT_SIZE=8192
FREQUENCIES=[31,62,125,250,500,1000,2000,4000,8000,16000]
TOPIC="ha_spectrum/state"

def get_source(session):
    response=session.get(f"{HA_URL}/api/states/{ENTITY}",timeout=6)
    response.raise_for_status()
    state=response.json()
    source=state.get("attributes",{}).get("media_content_id")
    if state.get("state")!="playing" or not isinstance(source,str):
        return None
    parsed=urlparse(source)
    if parsed.scheme not in ("http","https") or not parsed.hostname or parsed.username or parsed.password:
        return None
    return source

def levels(pcm):
    samples=np.frombuffer(pcm,dtype="<i2").astype(np.float32)/32768.0
    if len(samples)!=FFT_SIZE: return None
    # Normalize window amplitude to keep FFT bins comparable.
    spectrum=np.abs(np.fft.rfft(samples*np.hanning(FFT_SIZE)))/(FFT_SIZE/2)
    hz=np.fft.rfftfreq(FFT_SIZE,1/SAMPLE_RATE)
    edges=[20]+[(FREQUENCIES[i]*FREQUENCIES[i+1])**.5 for i in range(9)]+[20000]
    values=[]
    for low,high in zip(edges,edges[1:]):
        band=spectrum[(hz>=low)&(hz<high)]
        amplitude=float(np.sqrt(np.mean(band**2))) if len(band) else 0
        db=20*np.log10(max(amplitude,1e-8))
        values.append(round(float(np.clip((db+80)/65,0,1)),3))
    return values

def publish(client,bands,source):
    payload={"levels":bands,"source_entity":ENTITY,"source_media_id":source,
             "sampled_at":datetime.now(timezone.utc).isoformat()}
    client.publish(TOPIC,json.dumps(payload),qos=0,retain=False)

def stop(proc):
    if proc and proc.poll() is None:
        proc.kill()
    if proc:
        proc.wait(timeout=5)

def main():
    logging.basicConfig(level=logging.INFO)
    session=requests.Session()
    session.headers.update({"Authorization":f"Bearer {HA_TOKEN}"})
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if os.getenv("MQTT_USER"):
        client.username_pw_set(os.environ["MQTT_USER"],os.getenv("MQTT_PASSWORD",""))
    client.connect(HOST,PORT,60)
    client.loop_start()
    client.publish("homeassistant/sensor/ha_spectrum_levels/config",json.dumps({
        "name":"HA Spectrum Levels","unique_id":"ha_spectrum_levels",
        "state_topic":TOPIC,"value_template":"{{ value_json.sampled_at }}",
        "json_attributes_topic":TOPIC,"icon":"mdi:equalizer","expire_after":10
    }),qos=1,retain=True)
    current=None
    proc=None
    buffer=bytearray()
    next_poll=0
    try:
        while True:
            if time.monotonic()>=next_poll:
                try: desired=get_source(session)
                except Exception as exc:
                    logging.warning("HA state unavailable: %s",exc)
                    desired=None
                next_poll=time.monotonic()+2
                if desired!=current or (proc is not None and proc.poll() is not None):
                    stop(proc)
                    proc=None
                    buffer.clear()
                    current=desired
                    publish(client,[0]*10,"")
                    if desired:
                        logging.info("Starting parallel radio analysis")
                        proc=subprocess.Popen(["ffmpeg","-nostdin","-loglevel","error",
                           "-rw_timeout","5000000","-i",desired,"-vn","-ac","1",
                           "-ar",str(SAMPLE_RATE),"-f","s16le","pipe:1"],
                           stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            if proc is None:
                time.sleep(.1)
                continue
            # Avoid blocking indefinitely on stalled network streams.
            ready,_,_=select.select([proc.stdout],[],[],.3)
            if not ready: continue
            pcm=proc.stdout.read1(FFT_SIZE*2)
            if not pcm:
                stop(proc);proc=None;current=None
                time.sleep(1)
                continue
            # Accumulate full PCM windows; partial reads must not lose alignment.
            buffer.extend(pcm)
            while len(buffer)>=FFT_SIZE*2:
                frame=bytes(buffer[:FFT_SIZE*2])
                del buffer[:FFT_SIZE*2]
                computed=levels(frame)
                if computed is not None: publish(client,computed,current)
    except KeyboardInterrupt:
        pass
    finally:
        stop(proc);client.loop_stop();client.disconnect()

if __name__=="__main__":main()
