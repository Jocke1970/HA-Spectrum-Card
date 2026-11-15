"""Offline unit tests: no HA, MQTT broker or radio station required."""
import importlib.util
import os
import pathlib
import unittest
from unittest.mock import Mock
import numpy as np

os.environ.setdefault("HA_URL","http://homeassistant.local:8123")
os.environ.setdefault("HA_TOKEN","test-only")
MODULE=pathlib.Path(__file__).resolve().parents[1]/"apps"/"spectrum_fft"/"analyzer.py"
spec=importlib.util.spec_from_file_location("spectrum_analyzer",MODULE)
analyzer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer)

class SourceTests(unittest.TestCase):
    def source(self,state,url):
        response=Mock()
        response.json.return_value={"state":state,"attributes":{"media_content_id":url}}
        session=Mock()
        session.get.return_value=response
        value=analyzer.get_source(session)
        session.get.assert_called_once()
        return value

    def test_radio_url(self):
        url="http://fm02-ice.stream.khz.se/fm02_mp3"
        self.assertEqual(self.source("playing",url),url)

    def test_spotify_not_audio_stream(self):
        self.assertIsNone(self.source("playing","spotify:track:7FCiDC7ojdm19CJePq6QAe"))

    def test_paused_radio(self):
        self.assertIsNone(self.source("paused","https://radio.example/live.mp3"))

    def test_reject_non_http_and_embedded_password(self):
        for url in ("file:///etc/passwd","ftp://example.org/stream","http://user:pass@host/live"):
            with self.subTest(url=url):
                self.assertIsNone(self.source("playing",url))

class FFTTests(unittest.TestCase):
    def tone(self,hz,amplitude=.75):
        t=np.arange(analyzer.FFT_SIZE)/analyzer.SAMPLE_RATE
        pcm=np.asarray(np.sin(2*np.pi*hz*t)*amplitude*32767,dtype="<i2")
        return analyzer.levels(pcm.tobytes())

    def test_ten_bands_finite_bounded(self):
        result=self.tone(1000)
        self.assertEqual(len(result),10)
        self.assertTrue(all(0<=v<=1 and np.isfinite(v) for v in result))

    def test_1khz_is_dominant(self):
        self.assertEqual(int(np.argmax(self.tone(1000))),5)

    def test_16khz_is_represented(self):
        self.assertEqual(int(np.argmax(self.tone(16000))),9)

    def test_low_band(self):
        self.assertEqual(int(np.argmax(self.tone(31))),0)

    def test_silence(self):
        self.assertEqual(analyzer.levels(bytes(analyzer.FFT_SIZE*2)),[0.0]*10)

    def test_partial_frame(self):
        self.assertIsNone(analyzer.levels(bytes(100)))

if __name__=="__main__":
    unittest.main()
