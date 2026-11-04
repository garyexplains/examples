# python3 -m venv needle-env
# source needle-env/bin/activate
# pip install "cactus-needle[mic]" piper-tts
# Voice assistant: always-on "hey needles" wake word -> tools -> spoken answer.
#
# Bluetooth speaker: make it the default output once after pairing:
#   wpctl set-default $(wpctl status | grep bluez | cut -d. -f1 | grep -o '[0-9]*')
import needle
import os
import subprocess
import tempfile
import wave
from pathlib import Path

@needle.tool
def get_cpu_temperature():

    """Return the current CPU temperature of this Raspberry Pi in Celsius."""

    out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)

    return {"temperature_c": float(out.split("=")[1].split("'")[0])}


agent = needle.Needle(tools=[get_cpu_temperature], stateless=True)

SAMPLE_RATE = 16000          # what Whistle wants
ACTIVATION = "hey needles"   # wake word; spoken e.g. "hey needles, what's the CPU temperature"
WAKE_KEYWORDS = ["hey needles", "temperature", "CPU"]
SILENCE_SECONDS = 1.8        # how long the command may trail off before it runs
ANSWER_HUSH_SECONDS = 8.0    # after answering, ignore this much captured audio:
                             # the speaker's own voice echoes into the mic

TTS_MODEL = Path(__file__).resolve().parent / "voices" / "en_US-lessac-medium"
_tts_voice = None


def speak(text):
    """Say text out loud with Piper TTS through the default PipeWire sink."""
    global _tts_voice
    text = (text or "").strip()
    if not text or text in ("[]", "{}"):
        return "nothing to say"
    if _tts_voice is None:
        _tts_voice = _load_tts()
        if _tts_voice is None:
            return "TTS is not installed"
    path = tempfile.mktemp(prefix="say-", suffix=".wav")
    try:
        with wave.open(path, "wb") as wav:
            _tts_voice.synthesize_wav(text, wav)
        if os.path.getsize(path) > 44:      # header written means audio existed
            subprocess.run(["aplay", "-q", path], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            return "TTS produced no audio"
    except (wave.Error, EOFError, RuntimeError) as error:
        print(f"  TTS skipped: {error}", flush=True)
        return "TTS failed"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    return "said"


def _load_tts(model=TTS_MODEL):
    """Load the Piper voice as a module-level singleton; returns None if missing."""
    global _tts_voice
    if _tts_voice is not None:
        return _tts_voice
    try:
        import piper
    except ImportError:
        return None
    onnx, config = f"{model}.onnx", f"{model}.onnx.json"
    if not (Path(onnx).exists() and Path(config).exists()):
        print(f"  TTS voice not found at {onnx} — downloading...", flush=True)
        for url, target in (
            ("https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx", onnx),
            ("https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json", config),
        ):
            subprocess.run(["curl", "-sSL", "-o", target, url], check=True)
    _tts_voice = piper.PiperVoice.load(onnx, config)
    return _tts_voice


def sentences_for_results(results):
    """Turn tool results into speakable full sentences."""
    sentences = []
    for result in results or []:
        if isinstance(result, dict) and "temperature_c" in result:
            temp = result["temperature_c"]
            if temp is not None:
                sentences.append(f"The Raspberry Pi CPU temperature is {temp:g} degrees Celsius.")
            else:
                sentences.append("Sorry, I could not read the CPU temperature.")
        elif isinstance(result, dict) and "error" in result:
            sentences.append("Sorry, I could not complete that request.")
        elif isinstance(result, str):
            sentences.append(result)
    return sentences


def mic_loop(agent):
    """Always-on: stream the mic through Whistle, gate on the wake word,
    and run everything said after it as an agent query, spoken back."""
    import numpy
    import queue
    import sounddevice
    import soxr

    # Preload TTS while the loop is setting up, so the first answer is streamed
    _load_tts()

    heard = queue.Queue()
    native = int(sounddevice.query_devices(kind="input")["default_samplerate"])
    resampler = None if native == SAMPLE_RATE else soxr.ResampleStream(
        native, SAMPLE_RATE, 1, dtype="float32", quality="HQ")

    def capture(samples, *rest):
        heard.put(resampler.resample_chunk(samples[:, 0]) if resampler
                  else samples[:, 0].copy())

    def chunks():
        block, held = [], 0
        while True:
            data = heard.get()
            if data is None:
                if block:
                    yield numpy.concatenate(block)
                return
            block.append(data)
            held += len(data)
            if held >= SAMPLE_RATE:      # hand Whistle ~1 s at a time
                yield numpy.concatenate(block)
                block, held = [], 0

    armed, command, quiet, received, hush = False, "", 0.0, 0.0, 0.0
    with sounddevice.InputStream(samplerate=native, channels=1,
                                 dtype="float32", callback=capture):
        print(f'● always-on: say "{ACTIVATION}, ..." — Ctrl-C to quit', flush=True)
        for step in needle.stream(chunks(), language="en", keywords=WAKE_KEYWORDS):
            text = step["text"].strip()
            spoken_seconds = step["received"] - received
            received = step["received"]

            if not armed:
                if hush > 0:
                    hush -= spoken_seconds   # discard the echo of our own answer
                    continue
                lowered = step["text"].lower()
                index = lowered.find(ACTIVATION)
                if index >= 0:
                    armed = True
                    command = step["text"][index + len(ACTIVATION):].strip(" ,.!?")
                    quiet = 0.0
                    print(f'\n● "{ACTIVATION}" — {command or "listening…"}', end="", flush=True)
                continue

            if text:
                command = f"{command} {text}".strip()
                quiet = 0.0
                print(f"  {command}", end="\r", flush=True)
            else:
                quiet += spoken_seconds   # nothing new committed this second
            if quiet < SILENCE_SECONDS:
                continue

            armed, spoken, command, quiet = False, command, "", 0.0
            print()
            if not spoken:
                print("  (nothing commanded after the wake word)")
                continue
            try:
                answer = agent.run(spoken)
            except Exception as error:
                print(f"  agent error: {error}")
                speak("Sorry, something went wrong.")
                continue
            print(f"> {spoken}")
            sentences = sentences_for_results(answer["results"])
            if sentences:
                print(f"🔊 {' '.join(sentences)}", flush=True)
                reply = " ".join(sentences)
            else:
                reply = "Sorry, I could not complete that request."
                print(f"  (no tool results to speak: {answer['results']})", flush=True)
            try:
                speak(reply)
            finally:
                hush = ANSWER_HUSH_SECONDS


if __name__ == "__main__":
    try:
        mic_loop(agent)
    except KeyboardInterrupt:
        print("\nbye")
