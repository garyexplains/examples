# needles.py — voice assistant on a Raspberry Pi 500+
#
# python3 -m venv needle-env && source needle-env/bin/activate
# pip install "cactus-needle[mic]" requests piper-tts
# sudo apt install libportaudio2
#
# Always-on "hey needles" wake word -> needle agent with tools -> Piper TTS answer.
# Bluetooth speaker: after pairing, wpctl set-default <sink-id> (see wpctl status)
import datetime
import random
import re
import xml.etree.ElementTree as ET
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import needle
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
JOKES_URL = "https://icanhazdadjoke.com/"
NEWS_URL = "https://feeds.bbci.co.uk/news/rss.xml"
WEATHER_TIMEOUT = (5, 15)

# Comprehensive mapping of WMO codes to Open-Meteo English descriptions
WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}
def get_weather_description(code: int) -> str:
    """Returns the English text description for a given WMO weather code."""
    return WMO_WEATHER_CODES.get(code, f"Unknown weather code ({code})")

def get_coordinates(city_name):
  """Turn a city name into latitude and longitude."""
  response = requests.get(GEOCODING_URL,
                          params={"name": city_name, "count": 1},
                          timeout=WEATHER_TIMEOUT)
  response.raise_for_status()
  results = response.json().get("results")
  if results:
    return results[0]["latitude"], results[0]["longitude"]
  return None, None


def get_weather_by_city(city_name):
  """Fetch current weather for a city name."""
  lat, lon = get_coordinates(city_name)
  if lat is None or lon is None:
    return {"city": city_name, "not_found": True}

  response = requests.get(
      FORECAST_URL,
      params={
          "latitude": lat,
          "longitude": lon,
          "current": "temperature_2m,weather_code",
          "timezone": "auto",
      },
      timeout=WEATHER_TIMEOUT,
  )
  response.raise_for_status()
  current = response.json()["current"]
  return {"city": city_name,
          "temp_c": current["temperature_2m"],
          "sky": get_weather_description(current["weather_code"])}


@needle.tool
def get_weather(city: str):
    "Get the current weather for a city."

    return get_weather_by_city(city)

@needle.tool
def get_cpu_temperature():

    """Return the current CPU temperature of this Raspberry Pi in Celsius."""

    out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)

    return {"temperature_c": float(out.split("=")[1].split("'")[0])}


@needle.tool
def get_disk_space():
    """Get total, used and free space on the root filesystem in decimal gigabytes."""

    total, used, free = shutil.disk_usage("/")
    gb = 1_000_000_000
    return {"disk_total_gb": round(total / gb, 1),
            "disk_used_gb": round(used / gb, 1),
            "disk_free_gb": round(free / gb, 1)}


@needle.tool
def get_free_memory():
    """Get available system memory in gigabytes."""

    with open("/proc/meminfo") as meminfo:
        for line in meminfo:
            if line.startswith("MemAvailable:"):
                available_kb = int(line.split()[1])
                return {"memory_free_gb": round(available_kb * 1024 / 1_000_000_000, 1)}
    return {"memory_free_gb": None}


@needle.tool
def get_time():
    """Get the current local time and date."""

    now = datetime.datetime.now()
    return {"time": now.strftime("%H:%M"), "date": now.strftime("%A %-d %B")}


_HOURS = ("twelve", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine", "ten", "eleven", "twelve")
_MINUTES = ("o'clock", "five past", "ten past", "quarter past", "twenty past",
            "twenty five past", "half past", "twenty five to", "twenty to",
            "quarter to", "ten to", "five to")
EXACT_TIME_RE = re.compile(r"\b(?:exact|precise)\b.*\btime\b|\btime\b.*\b(?:exact|precise)\b")
CASUAL_TIME_RE = re.compile(
    r"\b(?:what(?:'s| is) the time|what time is it|tell me the time|got the time)\b")


def casual_time_sentence(now=None):
    """13:32 becomes "It's half past one." — minute rounded to the nearest five."""
    now = now or datetime.datetime.now()
    hour, minute = now.hour % 12 or 12, now.minute
    bucket = round(minute / 5) * 5
    if bucket == 60:
        hour = hour % 12 + 1
        bucket = 0
    if bucket == 0:
        phrase = f"{_HOURS[hour]} o'clock"
    elif bucket <= 30:
        phrase = f"{_MINUTES[bucket // 5]} {_HOURS[hour]}"
    else:
        phrase = f"{_MINUTES[bucket // 5]} {_HOURS[hour % 12 + 1]}"
    return f"It's {phrase}."


@needle.tool
def coin_flip():
    """Flip a coin and tell heads or tails."""

    return {"coin": random.choice(("heads", "tails"))}


@needle.tool
def single_die():
    """Roll ONE six-sided die, a single die roll, one die only, never two dice.
    A die is the singular of dice."""

    return {"single_die": random.randint(1, 6)}


@needle.tool
def double_dice():
    """Roll TWO six-sided dice together in one throw, a double dice roll for a
    pair of two dice at once, showing both dice and their total."""

    first, second = random.randint(1, 6), random.randint(1, 6)
    return {"dice": [first, second], "total": first + second}


@needle.tool
def random_number(upper_bound: int = 100):
    """Pick a random number between 1 and the given maximum, inclusive."""

    if upper_bound < 1:
        raise ValueError(f"upper_bound must be at least 1, got {upper_bound}")
    return {"chosen": random.randint(1, upper_bound), "max": upper_bound}


_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}
_TENS_WORDS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_NUMBER_TOKEN_RE = re.compile(r"\d[\d,]*|[a-z]+")
RANDOM_REQUEST_RE = re.compile(
    r"\b(?:random number|pick (?:me )?a number|choose (?:me )?a number|give me a number)\b")


def _parse_number_tokens(tokens, start):
    """Parse a leading integer written as digits or ordinary English words."""
    if start >= len(tokens):
        return None, start
    token = tokens[start]
    if re.fullmatch(r"\d[\d,]*", token):
        return int(token.replace(",", "")), start + 1

    total = current = 0
    index, consumed, allow_and = start, False, False
    while index < len(tokens):
        token = tokens[index]
        if token in _NUMBER_WORDS:
            current += _NUMBER_WORDS[token]
            consumed, allow_and = True, False
        elif token in _TENS_WORDS:
            current += _TENS_WORDS[token]
            consumed, allow_and = True, False
        elif token == "hundred":
            current = max(current, 1) * 100
            consumed, allow_and = True, True
        elif token in ("thousand", "million"):
            scale = 1_000 if token == "thousand" else 1_000_000
            total += max(current, 1) * scale
            current = 0
            consumed, allow_and = True, True
        elif token == "and" and allow_and:
            allow_and = False
        else:
            break
        index += 1
    if not consumed:
        return None, start
    return total + current, index


def random_number_bound(text):
    """Return (has_explicit_bound, upper_bound) for a spoken random-number request."""
    tokens = [token.replace(",", "") for token in _NUMBER_TOKEN_RE.findall(text.lower().replace("-", " "))]
    for index, token in enumerate(tokens):
        if token == "between":
            lower, next_index = _parse_number_tokens(tokens, index + 1)
            if lower is None or next_index >= len(tokens) or tokens[next_index] != "and":
                return True, None
            upper, _ = _parse_number_tokens(tokens, next_index + 1)
            return True, upper if lower == 1 else None
        if token == "up" and index + 1 < len(tokens) and tokens[index + 1] == "to":
            upper, _ = _parse_number_tokens(tokens, index + 2)
            return True, upper
        if token == "from":
            lower, next_index = _parse_number_tokens(tokens, index + 1)
            if lower is None or next_index >= len(tokens) or tokens[next_index] != "to":
                return True, None
            upper, _ = _parse_number_tokens(tokens, next_index + 1)
            return True, upper if lower == 1 else None
    return False, 100


@needle.tool
def tell_joke():
    """Tell a random dad joke."""

    response = requests.get(JOKES_URL, headers={"Accept": "application/json",
                                                "User-Agent": "needles-assistant"},
                            timeout=10)
    response.raise_for_status()
    return {"joke": response.json().get("joke")}


@needle.tool
def get_headlines():
    """Get the top BBC News headlines."""

    response = requests.get(NEWS_URL, headers={"User-Agent": "needles-assistant"},
                            timeout=10)
    response.raise_for_status()
    titles = [item.findtext("title", "").strip()
              for item in ET.fromstring(response.content).iterfind(".//item")]
    headlines = [title for title in titles if title][:5]
    if not headlines:
        return {"headlines": [], "error": "no headlines in feed"}
    return {"source": "BBC News", "headlines": headlines}


SAMPLE_RATE = 16000          # what Whistle wants
ACTIVATION = "hey needles"   # wake word; spoken e.g. "hey needles, what's the weather in Lagos"
WAKE_KEYWORDS = ["hey needles", "weather", "temperature", "CPU", "joke", "news",
                 "coin", "dice", "random"]
SILENCE_SECONDS = 1.8        # how long the command may trail off before it runs
WAKE_BUFFER_SECONDS = 2.0    # retain partial wake-word text across stream steps

_ACTIVATION_PATTERN = r"[\W_]+".join(re.escape(word) for word in ACTIVATION.split())
ACTIVATION_RE = re.compile(r"(?<!\w)" + _ACTIVATION_PATTERN + r"(?!\w)", re.IGNORECASE)
HELP_PHRASES = ("help", "what can you do", "what can you do for me",
                "what can i ask", "what do you do", "what are you able to do")
HELP_REPLY = (
    "I can tell you the current weather in any city, the exact time, or a casual "
    "one like half past one, plus the CPU temperature, free disk space or memory, "
    "BBC headlines, a dad joke, a coin flip, a single die or double dice, "
    "or a random number. "
    "Say \"hey needles\" first, then just ask."
)

TOOLS = [get_weather, get_cpu_temperature, get_disk_space, get_free_memory,
         get_time, tell_joke, get_headlines,
         coin_flip, single_die, double_dice, random_number]

TTS_MODEL = Path(__file__).resolve().parent / "voices" / "en_US-lessac-medium"
_tts_voice = None


def consume_wake_text(buffer, text):
    """Append a committed transcript fragment and detect a wake phrase across chunks."""
    combined = f"{buffer} {text}".strip()[-160:]
    match = ACTIVATION_RE.search(combined)
    if match:
        command = combined[match.end():].strip(" ,.!?")
        return "", command, True
    return combined, "", False


def update_quiet_time(quiet, committed, pending, elapsed):
    """Only count silence when neither committed nor pending speech is present."""
    if committed or pending:
        return 0.0
    return quiet + max(0.0, elapsed)


def shortcut_reply(spoken):
    """Return a fixed local reply for help, time and random-number requests."""
    normalized = " ".join(spoken.lower().strip(" .!?,").split())
    if normalized in HELP_PHRASES:
        return HELP_REPLY
    if EXACT_TIME_RE.search(normalized):
        return sentences_for_results([get_time()])[0]
    if CASUAL_TIME_RE.search(normalized):
        return casual_time_sentence()
    if RANDOM_REQUEST_RE.search(normalized):
        has_bound, upper_bound = random_number_bound(normalized)
        if has_bound and upper_bound is None:
            return "Please give me a positive whole-number limit, such as one hundred."
        try:
            return sentences_for_results([random_number(upper_bound)])[0]
        except (TypeError, ValueError):
            return "Please give me a positive whole-number limit, such as one hundred."
    return None


def speak(text):
    """Say text out loud with Piper TTS through the default PipeWire sink."""
    global _tts_voice
    text = (text or "").strip()
    if not text or text in ("[]", "{}"):
        return "nothing to say"
    path = None
    try:
        if _tts_voice is None:
            _tts_voice = _load_tts()
            if _tts_voice is None:
                return "TTS is not installed"
        fd, path = tempfile.mkstemp(prefix="say-", suffix=".wav")
        os.close(fd)
        with wave.open(path, "wb") as wav:
            _tts_voice.synthesize_wav(text, wav)
        if os.path.getsize(path) > 44:      # header written means audio existed
            subprocess.run(["aplay", "-q", path], check=True, timeout=120,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                           text=True)
        else:
            return "TTS produced no audio"
    except Exception as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) and error.stderr else str(error)
        print(f"  TTS unavailable: {detail}", flush=True)
        return "TTS failed"
    finally:
        if path is not None:
            try:
                os.unlink(path)
            except OSError:
                pass
    return "said"


def _load_tts(model=TTS_MODEL):
    """Load the Piper voice once, downloading missing model files atomically."""
    global _tts_voice
    if _tts_voice is not None:
        return _tts_voice
    try:
        import piper
    except ImportError:
        return None
    model = Path(model)
    model.parent.mkdir(parents=True, exist_ok=True)
    onnx, config = Path(f"{model}.onnx"), Path(f"{model}.onnx.json")
    files = (
        ("https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx", onnx),
        ("https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json", config),
    )
    for url, target in files:
        if not target.is_file() or target.stat().st_size == 0:
            print(f"  downloading TTS voice file {target.name}...", flush=True)
            partial = target.with_name(target.name + ".part")
            try:
                with requests.get(url, stream=True, timeout=(10, 120),
                                  headers={"User-Agent": "needles-assistant"}) as response:
                    response.raise_for_status()
                    with partial.open("wb") as output:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                output.write(chunk)
                if partial.stat().st_size == 0:
                    raise RuntimeError(f"downloaded an empty TTS file: {target.name}")
                partial.replace(target)
            finally:
                partial.unlink(missing_ok=True)
    _tts_voice = piper.PiperVoice.load(str(onnx), str(config))
    return _tts_voice


def sentences_for_results(results):
    """Turn tool results into speakable full sentences."""
    sentences = []
    for result in results or []:
        if not isinstance(result, dict):
            sentences.append(str(result))
        elif "city" in result:
            city, temp, sky = result["city"], result.get("temp_c"), result.get("sky")
            if result.get("not_found"):
                sentences.append(f"Sorry, I could not find a city called {city}.")
            elif temp is not None:
                sky = (sky or "unknown conditions").lower()
                sky = {
                    "clear sky": "clear skies",
                    "mainly clear": "mostly clear skies",
                    "partly cloudy": "partly cloudy skies",
                    "overcast": "overcast skies",
                    "depositing rime fog": "freezing fog",
                }.get(sky, sky)
                sentences.append(f"In {city}, it is currently {temp:g} degrees Celsius, with {sky}.")
            else:
                sentences.append(f"Sorry, I could not get the weather for {city}.")
        elif "temperature_c" in result:
            temp = result["temperature_c"]
            if temp is not None:
                sentences.append(f"The Raspberry Pi CPU temperature is {temp:g} degrees Celsius.")
            else:
                sentences.append("Sorry, I could not read the CPU temperature.")
        elif "disk_free_gb" in result:
            free, total = result.get("disk_free_gb"), result.get("disk_total_gb")
            if free is not None and total is not None:
                sentences.append(f"The root filesystem has {free:g} gigabytes free out of {total:g}.")
            else:
                sentences.append("Sorry, I could not read the disk space.")
        elif "memory_free_gb" in result:
            memory = result["memory_free_gb"]
            if memory is not None:
                sentences.append(f"There are {memory:g} gigabytes of memory available.")
            else:
                sentences.append("Sorry, I could not read the memory.")
        elif "time" in result:
            sentences.append(f"It is {result['time']} on {result.get('date', 'today')}.")
        elif "joke" in result:
            if result["joke"]:
                sentences.append(f"Here goes: {result['joke']}")
            else:
                sentences.append("Sorry, the joke service is not answering.")
        elif "headlines" in result:
            headlines, source = result.get("headlines"), result.get("source", "BBC News")
            if headlines:
                joined = ". ".join(f"{number}. {title}" for number, title in enumerate(headlines, 1))
                sentences.append(f"Here are the top {len(headlines)} headlines from {source}. {joined}")
            else:
                sentences.append(f"Sorry, no headlines are available from {source} right now.")
        elif "coin" in result:
            sentences.append(f"The coin lands {result['coin']}.")
        elif "single_die" in result:
            roll = result["single_die"]
            if isinstance(roll, int) and 1 <= roll <= 6:
                sentences.append(f"The die shows {roll:g}.")
            else:
                sentences.append("Sorry, I could not roll the die.")
        elif "dice" in result:
            dice, total = result.get("dice"), result.get("total")
            if isinstance(dice, list) and len(dice) == 2 and all(isinstance(n, int) and 0 < n < 7 for n in dice) and total is not None:
                sentences.append(f"You rolled {dice[0]:g} and {dice[1]:g}, which makes {total:g}.")
            else:
                sentences.append("Sorry, I could not roll the dice.")
        elif "chosen" in result:
            chosen, top = result["chosen"], result.get("max", 100)
            if chosen is not None:
                sentences.append(f"Your random number between 1 and {top:g} is {chosen:g}.")
            else:
                sentences.append("Sorry, I could not pick a number.")
        elif "error" in result:
            sentences.append("Sorry, I could not complete that request.")
        else:
            sentences.append(" ".join(f"{key} {value}" for key, value in result.items()))
    return sentences


def mic_loop(agent):
    """Always-on: stream the mic through Whistle, gate on the wake word,
    and run everything said after it as an agent query, spoken back."""
    import numpy
    import queue
    import sounddevice
    import soxr
    import threading

    # Preload TTS while the loop is setting up, so the first answer is faster.
    try:
        if _load_tts() is None:
            print('  TTS unavailable; install "piper-tts" to enable voice output.', flush=True)
    except Exception as error:
        print(f"  TTS preload failed; will retry when needed: {error}", flush=True)

    # Bound memory and keep latency low if transcription temporarily falls behind.
    heard = queue.Queue(maxsize=12)
    native = int(sounddevice.query_devices(kind="input")["default_samplerate"])
    resampler = None if native == SAMPLE_RATE else soxr.ResampleStream(
        native, SAMPLE_RATE, 1, dtype="float32", quality="HQ")
    capture_lock = threading.Lock()
    capture_state = {"busy": False, "generation": 0}
    audio_overflow = threading.Event()

    def capture(samples, frames, time_info, status):
        if status:
            audio_overflow.set()
        with capture_lock:
            if capture_state["busy"]:
                return
            generation = capture_state["generation"]
        audio = (resampler.resample_chunk(samples[:, 0]) if resampler
                 else samples[:, 0].copy())
        if not len(audio):
            return
        with capture_lock:
            if (capture_state["busy"]
                    or generation != capture_state["generation"]):
                return
            try:
                heard.put_nowait((generation, audio))
            except queue.Full:
                # Drop the stale backlog and let the newest audio re-synchronize.
                capture_state["generation"] += 1
                generation = capture_state["generation"]
                while True:
                    try:
                        heard.get_nowait()
                    except queue.Empty:
                        break
                heard.put_nowait((generation, audio))
                audio_overflow.set()

    def chunks():
        block, held, generation = [], 0, None
        while True:
            next_generation, data = heard.get()
            if next_generation != generation:
                # Never combine pre-request audio with post-request audio.
                block, held, generation = [], 0, next_generation
            block.append(data)
            held += len(data)
            if held >= SAMPLE_RATE:      # hand Whistle ~1 s at a time
                yield numpy.concatenate(block)
                block, held = [], 0

    def pause_capture():
        with capture_lock:
            capture_state["busy"] = True
            capture_state["generation"] += 1
            while True:
                try:
                    heard.get_nowait()
                except queue.Empty:
                    break

    def resume_capture():
        with capture_lock:
            generation = capture_state["generation"]
            while True:
                try:
                    heard.get_nowait()
                except queue.Empty:
                    break
            # Let Whistle flush any pending tail while the mic is muted.
            silence = numpy.zeros(SAMPLE_RATE, dtype=numpy.float32)
            heard.put_nowait((generation, silence))
            heard.put_nowait((generation, silence.copy()))
            capture_state["busy"] = False

    def answer_command(spoken):
        """Handle one turn without recording tool activity or the assistant's voice."""
        pause_capture()
        try:
            print(f"> {spoken}")
            reply = shortcut_reply(spoken)
            if reply is None:
                try:
                    answer = agent.run(spoken)
                    sentences = sentences_for_results(answer["results"])
                    if sentences:
                        reply = " ".join(sentences)
                    else:
                        reply = "Sorry, I could not complete that request."
                        print(f"  (no tool results to speak: {answer['results']})", flush=True)
                    for result in answer["results"]:
                        if isinstance(result, dict) and "error" in result:
                            print(f"  tool error: {result['error']}", flush=True)
                except Exception as error:
                    print(f"  agent error: {error}", flush=True)
                    reply = "Sorry, something went wrong."

            print(f"🔊 {reply}", flush=True)
            status = speak(reply)
            if status != "said":
                print(f"  reply was not spoken ({status})", flush=True)
        finally:
            # Capture remains muted through tool execution and playback. Silence
            # chunks reset Whistle's stream without creating an audio backlog.
            resume_capture()

    armed, command, quiet, received = False, "", 0.0, 0.0
    wake_buffer, wake_idle = "", 0.0
    with sounddevice.InputStream(samplerate=native, channels=1,
                                 dtype="float32", callback=capture):
        print(f'● always-on: say "{ACTIVATION}, ..." — Ctrl-C to quit', flush=True)
        for step in needle.stream(chunks(), language="en", keywords=WAKE_KEYWORDS):
            text = (step.get("text") or "").strip()
            pending = (step.get("pending") or "").strip()
            spoken_seconds = max(0.0, step["received"] - received)
            received = step["received"]

            if audio_overflow.is_set():
                print("  warning: audio queue overflow; some input was dropped", flush=True)
                audio_overflow.clear()

            if not armed:
                if text:
                    wake_buffer, wake_command, activated = consume_wake_text(wake_buffer, text)
                    wake_idle = 0.0
                    if activated:
                        armed = True
                        command, quiet = wake_command, 0.0
                        print(f'\n● "{ACTIVATION}" — {command or "listening…"}', end="", flush=True)
                elif pending:
                    wake_idle = 0.0
                else:
                    wake_idle += spoken_seconds
                    if wake_idle >= WAKE_BUFFER_SECONDS:
                        wake_buffer, wake_idle = "", 0.0
                continue

            if text:
                command = f"{command} {text}".strip()
                print(f"  {command}", end="\r", flush=True)
            # Empty committed text can still have an unconfirmed speech tail.
            quiet = update_quiet_time(quiet, text, pending, spoken_seconds)
            if quiet < SILENCE_SECONDS:
                continue

            armed, spoken, command, quiet = False, command, "", 0.0
            wake_buffer, wake_idle = "", 0.0
            print()
            if not spoken:
                print("  (nothing commanded after the wake word)")
                continue
            answer_command(spoken)


def main():
    agent = needle.Needle(tools=TOOLS, stateless=True)
    try:
        mic_loop(agent)
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
