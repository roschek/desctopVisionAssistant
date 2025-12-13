import datetime
import wave
from pathlib import Path
from typing import Optional, Deque, Tuple

import os
import threading
import numpy as np
import soundcard as sc
import miniaudio as ma
import time
import collections

# --- Numpy 2.x compatibility for soundcard (uses np.fromstring in binary mode) ---
if hasattr(np, "fromstring"):
    _np_fromstring_original = np.fromstring  # type: ignore[attr-defined]

    def _np_fromstring_compat(string, dtype=float, count: int = -1, sep: str = ""):
        if sep == "":
            return np.frombuffer(string, dtype=dtype, count=count)
        return _np_fromstring_original(string, dtype=dtype, count=count, sep=sep)

    np.fromstring = _np_fromstring_compat  # type: ignore[assignment]
# -------------------------------------------------------------------------------


class AudioService:
    """
    Loopback capture helper:
    - background ring buffer (miniaudio WASAPI)
    - on demand: return last N seconds as WAV bytes
    - sync save fallback (soundcard)
    """

    def __init__(
        self,
        save_dir: str = "audio_captures",
        default_duration_sec: float = 8.0,
    ) -> None:
        self._save_dir = Path(save_dir)
        self._default_duration_sec = float(default_duration_sec)
        # Defaults (overridable via env)
        self._default_backend = "miniaudio"
        self._default_force_samplerate = 48000
        # Ring buffer length (seconds) — keep last ~40s
        self._buffer_duration_sec = 40.0
        self._recorder: Optional[_RingRecorder] = None

    # -------- Public API --------

    def record_and_save(self) -> Optional[str]:
        duration_sec = self._read_duration()
        backend = os.getenv("AUDIO_BACKEND", self._default_backend).strip().lower()
        if backend == "miniaudio":
            result = self._record_with_miniaudio(duration_sec)
            if result is not None:
                return result
            print("[AudioService] miniaudio capture failed, falling back to soundcard")
        return self._record_with_soundcard(duration_sec)

    def _record_with_soundcard(self, duration_sec: float) -> Optional[str]:
        mic = self._select_loopback_microphone()
        if mic is None:
            print("[AudioService] Loopback device not found (soundcard)")
            return None

        samplerate = self._read_samplerate_override_soundcard(mic)
        num_frames = int(duration_sec * samplerate)

        print(
            f"[AudioService] (soundcard) Loopback capture: device={mic.name}, sr={samplerate}, "
            f"duration={duration_sec}s, frames={num_frames}"
        )

        try:
            data = mic.record(samplerate=samplerate, numframes=num_frames)
        except Exception as e:
            print(f"[AudioService] Record error (soundcard): {e}")
            return None

        return self._save_wav(data, samplerate)

    def ensure_recorder_running(self) -> None:
        """Ensure background recorder is active (miniaudio-only)."""
        if self._recorder and self._recorder.is_alive():
            return
        backend = os.getenv("AUDIO_BACKEND", self._default_backend).strip().lower()
        if backend != "miniaudio":
            print("[AudioService] Background recording is miniaudio-only; set AUDIO_BACKEND=miniaudio")
            return
        self._recorder = _RingRecorder(
            buffer_seconds=self._buffer_duration_sec,
            samplerate_hint=self._default_force_samplerate,
        )
        self._recorder.start()

    def get_last_audio_wav_bytes(self, seconds: float = 30.0) -> Optional[bytes]:
        """
        Return last N seconds as WAV bytes. Uses background ring buffer.
        """
        if not self._recorder or not self._recorder.is_alive():
            print("[AudioService] Recorder not running; starting now")
            self.ensure_recorder_running()
            return None
        pcm_bytes, sr, channels = self._recorder.get_last_pcm(seconds)
        if pcm_bytes is None:
            print("[AudioService] No data in buffer")
            return None
        try:
            with wave.open(self._temp_wav_path(), "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(pcm_bytes)
            with open(self._temp_wav_path(), "rb") as f:
                return f.read()
        except Exception as e:
            print(f"[AudioService] Failed to build WAV bytes: {e}")
            return None

    def _temp_wav_path(self) -> str:
        self._save_dir.mkdir(parents=True, exist_ok=True)
        return str(self._save_dir / "temp_last.wav")

    def _record_with_miniaudio(self, duration_sec: float) -> Optional[str]:
        devices = ma.Devices(backends=[ma.Backend.WASAPI])
        captures = devices.get_captures()
        if not captures:
            print("[AudioService] miniaudio: no capture devices found")
            return None

        hint = os.getenv("AUDIO_DEVICE_HINT", "").strip().lower()

        def pick_dev() -> dict:
            # 1) explicit hint
            if hint:
                for d in captures:
                    if hint in d["name"].lower():
                        return d
            # 2) Stereo Mix / Loopback / Cable
            keywords = ["stereo mix", "loopback", "virtual cable", "cable output"]
            for kw in keywords:
                for d in captures:
                    if kw in d["name"].lower():
                        return d
            # 3) first available
            return captures[0]

        chosen = pick_dev()

        # Determine sample rate and channels from formats; fallback to defaults
        sr_from_dev = None
        ch_from_dev = None
        for fmt in chosen.get("formats", []):
            sr_from_dev = fmt.get("samplerate", sr_from_dev)
            ch_from_dev = fmt.get("channels", ch_from_dev)
            if sr_from_dev and ch_from_dev:
                break

        samplerate = self._read_samplerate_override_miniaudio(chosen, sr_from_dev)
        channels = max(1, min(2, ch_from_dev or 2))

        print(
            f"[AudioService] (miniaudio) Loopback capture: device={chosen['name']}, sr={samplerate}, "
            f"ch={channels}, duration={duration_sec}s"
        )

        buffers: list[bytes] = []

        def capture_gen():
            while True:
                data = yield
                buffers.append(bytes(data))

        gen = capture_gen()
        next(gen)

        try:
            with ma.CaptureDevice(
                input_format=ma.SampleFormat.SIGNED16,
                nchannels=channels,
                sample_rate=samplerate,
                device_id=chosen["id"],
                backends=[ma.Backend.WASAPI],
            ) as cap:
                cap.start(gen)
                time.sleep(duration_sec)
                cap.stop()
        except Exception as e:
            print(f"[AudioService] Record error (miniaudio): {e}")
            return None

        if not buffers:
            print("[AudioService] miniaudio: empty recording")
            return None

        audio_i16 = np.frombuffer(b"".join(buffers), dtype=np.int16)
        if channels > 0:
            audio_i16 = audio_i16.reshape(-1, channels)
        audio_f = audio_i16.astype(np.float32) / 32767.0
        return self._save_wav(audio_f, samplerate)

    def _select_loopback_microphone(self):
        devices = sc.all_microphones(include_loopback=True)
        if not devices:
            return None

        hint = os.getenv("AUDIO_DEVICE_HINT", "").strip().lower()
        default_speaker_name = ""
        try:
            default_speaker_name = sc.default_speaker().name.lower()
        except Exception:
            pass

        # Priority: exact hint -> loopback matching default speaker -> first loopback -> first device
        if hint:
            for d in devices:
                if hint in d.name.lower():
                    print(f"[AudioService] Selected via AUDIO_DEVICE_HINT: {d.name}")
                    return d

        loopbacks = [d for d in devices if getattr(d, "isloopback", False)]
        if default_speaker_name:
            for d in loopbacks:
                nm = d.name.lower()
                if default_speaker_name in nm or nm in default_speaker_name:
                    print(f"[AudioService] Loopback matches default speaker: {d.name}")
                    return d

        if loopbacks:
            print(f"[AudioService] Using first loopback: {loopbacks[0].name}")
            return loopbacks[0]

        print(f"[AudioService] No loopback found, fallback: {devices[0].name}")
        return devices[0]

    def _read_duration(self) -> float:
        raw = os.getenv("AUDIO_DURATION", "").strip()
        if not raw:
            return self._default_duration_sec
        try:
            val = float(raw)
            return val if val > 0 else self._default_duration_sec
        except ValueError:
            return self._default_duration_sec

    def _read_samplerate_override_soundcard(self, mic) -> int:
        raw = os.getenv("AUDIO_FORCE_SAMPLERATE", "").strip()
        if raw:
            try:
                sr = int(raw)
                if sr > 0:
                    return sr
            except ValueError:
                print(f"[AudioService] WARNING: invalid AUDIO_FORCE_SAMPLERATE='{raw}'")
        try:
            sr_dev = int(mic.samplerate)
            if sr_dev > 0:
                return sr_dev
        except Exception:
            pass
        return self._default_force_samplerate

    def _read_samplerate_override_miniaudio(self, dev, sr_from_dev: Optional[int] = None) -> int:
        raw = os.getenv("AUDIO_FORCE_SAMPLERATE", "").strip()
        if raw:
            try:
                sr = int(raw)
                if sr > 0:
                    return sr
            except ValueError:
                print(f"[AudioService] WARNING: invalid AUDIO_FORCE_SAMPLERATE='{raw}'")
        if sr_from_dev and sr_from_dev > 0:
            return int(sr_from_dev)
        return self._default_force_samplerate

    def _save_wav(self, data: np.ndarray, samplerate: int) -> Optional[str]:
        audio_2d = self._ensure_2d(data)
        frames, channels = audio_2d.shape
        if frames == 0:
            print("[AudioService] Empty recording")
            return None

        audio_2d = np.clip(audio_2d, -1.0, 1.0)
        audio_i16 = (audio_2d * 32767.0).astype(np.int16)

        self._save_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self._save_dir / f"audio_capture_{ts}.wav"

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(int(samplerate))
            wf.writeframes(audio_i16.tobytes())

        print(f"[AudioService] WAV saved: {path} (frames={frames}, ch={channels})")
        return str(path)

    @staticmethod
    def _ensure_2d(audio):
        if audio.ndim == 1:
            return audio.reshape(-1, 1)
        return audio


class _RingRecorder(threading.Thread):
    """
    Background recorder on miniaudio (WASAPI capture); stores raw PCM16 bytes in a ring buffer.
    """

    def __init__(self, buffer_seconds: float, samplerate_hint: int) -> None:
        super().__init__(daemon=True)
        self.buffer_seconds = buffer_seconds
        self.samplerate_hint = samplerate_hint
        self._lock = threading.Lock()
        self._pcm: Deque[bytes] = collections.deque()
        self._total_bytes = 0
        self._max_bytes = None  # type: Optional[int]
        self._sr = samplerate_hint
        self._channels = 2
        self._stop_flag = threading.Event()

    def run(self) -> None:
        try:
            devices = ma.Devices(backends=[ma.Backend.WASAPI])
            captures = devices.get_captures()
            if not captures:
                print("[RingRecorder] capture devices not found")
                return
            chosen = captures[0]
            # Use the first supported format
            fmt = chosen.get("formats", [{}])[0]
            sr = int(fmt.get("samplerate", self.samplerate_hint) or self.samplerate_hint)
            ch = int(fmt.get("channels", 2) or 2)
            self._sr = sr
            self._channels = ch
            self._max_bytes = int(self.buffer_seconds * self._sr * self._channels * 2)

            buffers: list[bytes] = []

            def gen():
                while True:
                    data = yield
                    with self._lock:
                        self._pcm.append(bytes(data))
                        self._total_bytes += len(data)
                        while self._max_bytes is not None and self._total_bytes > self._max_bytes and self._pcm:
                            dropped = self._pcm.popleft()
                            self._total_bytes -= len(dropped)
                    if self._stop_flag.is_set():
                        return

            g = gen()
            next(g)

            with ma.CaptureDevice(
                input_format=ma.SampleFormat.SIGNED16,
                nchannels=ch,
                sample_rate=sr,
                backends=[ma.Backend.WASAPI],
            ) as cap:
                cap.start(g)
                while not self._stop_flag.is_set():
                    time.sleep(0.1)
                cap.stop()
        except Exception as e:
            print(f"[RingRecorder] Error: {e}")

    def stop(self) -> None:
        self._stop_flag.set()

    def get_last_pcm(self, seconds: float) -> Tuple[Optional[bytes], int, int]:
        with self._lock:
            if not self._pcm:
                return None, self._sr, self._channels
            needed = int(seconds * self._sr * self._channels * 2)
            data = b"".join(self._pcm)
            if len(data) > needed > 0:
                data = data[-needed:]
            return data, self._sr, self._channels

