# Learning Needle: from a Python tool to a voice assistant

This folder is a small teaching project built around [Cactus Needle](https://github.com/cactus-compute/needle). It starts with a single Python tool and gradually adds web APIs, microphone input, streaming speech recognition, and text-to-speech.

The scripts are **standalone examples**—run one at a time. The learning order is:

1. [`simple.py`](#1-simplepy): give Needle one local Python tool.
2. [`weather.py`](#2-weatherpy): add a web API and a second tool.
3. [`voice_simple.py`](#3-voice_simplepy): record a push-to-talk request and transcribe it.
4. [`voice.py`](#4-voicepy): listen continuously for a wake phrase.
5. [`voice_and_tts.py`](#5-voice_and_ttspy): speak the result with Piper TTS.
6. [`needles.py`](#6-needlespy): combine the services and voice features into the full assistant.

## What you will learn

- How a `@needle.tool` Python function becomes a tool the model can call.
- How `Needle.run()` selects and executes tools from a natural-language request.
- How to combine local tools with web APIs.
- How to move from recorded speech to streaming microphone input.
- How wake phrases, turn-end detection, and audio buffering fit into a voice loop.
- How to turn structured tool results into spoken sentences.

## Requirements and setup

These examples target a Raspberry Pi running Raspberry Pi OS. The CPU-temperature tool calls `vcgencmd`, so it is Pi-specific. Voice examples use the default system microphone; TTS examples play through the default audio output.

Create and activate a virtual environment from this folder:

```bash
python3 -m venv needle-env
source needle-env/bin/activate
python -m pip install --upgrade pip
```

The smallest example needs only Needle:

```bash
python -m pip install cactus-needle
```

`weather.py` and `needles.py` use `requests` for their web services:

```bash
python -m pip install requests
```

For microphone examples, install Needle’s microphone extra and the system PortAudio library:

```bash
python -m pip install "cactus-needle[mic]"
sudo apt install libportaudio2
```

The extra provides the Python audio, array, and resampling dependencies. PortAudio is the system library used by microphone capture.

For `voice_and_tts.py` and `needles.py`, install Piper:

```bash
python -m pip install piper-tts
```

Or install everything for all six examples in one go:

```bash
python -m pip install "cactus-needle[mic]" requests piper-tts
sudo apt install libportaudio2
```

Needle may download its native engine and model files the first time it runs. The speech recognizer and Piper voice may also need model files, so allow an internet connection and some time for first-run downloads.

## The central idea: Python tools

A tool is an ordinary Python function marked with `@needle.tool`:

```python
@needle.tool
def get_cpu_temperature():
    """Return the current CPU temperature of this Raspberry Pi in Celsius."""
    ...
```

Needle uses the function name, docstring, and type annotations to describe the available tool to its model. The program supplies those functions when it creates an agent:

```python
agent = needle.Needle(tools=[get_cpu_temperature])
answer = agent.run("How hot is this Raspberry Pi?")
print(answer["results"])
```

The model decides whether a tool is appropriate; Python executes the selected function. `answer["results"]` contains the actual tool results. In later examples, the speech code either prints these results or turns them into a spoken sentence.

## 1. `simple.py`

**The first tool.** This is the smallest example: one tool reads the Pi CPU temperature by running `vcgencmd measure_temp`, and Needle calls it in response to a fixed prompt.

Run it with:

```bash
python3 simple.py
```

Look for:

- `@needle.tool`: registers `get_temperature()` as a tool.
- `subprocess.check_output(...)`: calls the Raspberry Pi command-line utility.
- `needle.Needle(tools=[...])`: gives the tool to an agent.
- `agent.run(...)`: asks Needle to answer the prompt, using the tool if appropriate.

This script runs its example immediately when executed. It is intended to be read and modified as a first exercise—for example, change the question or add another tool.

## 2. `weather.py`

**Two tools and a web API.** This example keeps the CPU-temperature tool and adds `get_weather(city)`. The weather tool:

1. Searches the Open-Meteo geocoding API for the city’s latitude and longitude.
2. Requests current temperature and WMO weather code from Open-Meteo’s forecast API.
3. Converts the WMO code into an English description such as “Overcast” or “Light rain.”

Open-Meteo does not require an API key for this example, but the Pi needs internet access. The script runs a London weather query, calls `agent.reset()`, then asks for the CPU temperature. Resetting separates the two unrelated requests in the agent’s conversation.

```bash
python3 weather.py
```

**Teaching caveat:** `get_weather_by_city()` returns a string when no city is found, but `get_weather()` then treats the result as forecast JSON. An unknown city can therefore produce a tool error rather than a friendly “city not found” result. The fuller `needles.py` example handles that case explicitly. This early example also does not set HTTP timeouts.

## 3. `voice_simple.py`

**Push-to-talk speech input.** This is the simplest voice interaction. It records a clip, transcribes it with Needle’s Whistle speech recognizer, passes the transcript to the CPU-temperature agent, and prints the result. It does not speak the answer aloud.

```bash
python3 voice_simple.py
```

At the prompt:

1. Press Enter to start a recording.
2. Say something like “What’s the CPU temperature?”
3. Press Enter again to stop recording.
4. Enter `q` at the next prompt to quit.

The `record()` helper handles microphone capture and resampling; `needle.transcribe()` converts the recording to text. The `keywords` argument biases recognition toward “CPU” and “temperature.” The transcript is then sent to `agent.run()`.

## 4. `voice.py`

**Always-on wake phrase, text output.** This version continuously streams microphone audio through Whistle and waits for **“hey needles.”** After the wake phrase, say a request such as:

> Hey needles, what is the CPU temperature?

After a short pause, Needle runs the CPU-temperature tool and prints the results. This script does **not** use TTS.

The audio path is more involved than push-to-talk:

1. `sounddevice.InputStream` captures microphone audio.
2. Audio is converted to 16 kHz mono for Whistle when needed.
3. A queue and chunk generator feed roughly one-second blocks to `needle.stream()`.
4. A rolling transcript buffer detects a wake phrase even when its words arrive in different stream steps.
5. Whistle’s pending transcript is considered before the script decides the user has finished speaking.
6. Capture pauses while the agent runs, so speech during a tool call is discarded instead of building up and being processed later.

The script uses a bounded queue and reports capture/queue overflows. The wake phrase is recognized from the transcript—`WAKE_KEYWORDS` only biases speech recognition; it is not a separate wake-word detector. End-of-turn detection uses transcript/pending-text state, not a dedicated voice-activity detector. Press Ctrl-C to stop the script. Install the microphone extra and `libportaudio2` as described above.

## 5. `voice_and_tts.py`

**Always-on wake phrase with spoken CPU results.** This adds Piper text-to-speech to the CPU-temperature assistant. After a successful tool call, the result is formatted as a sentence—such as “The Raspberry Pi CPU temperature is 42 degrees Celsius”—and played through `aplay` using the system’s default audio output.

```bash
python3 voice_and_tts.py
```

The Piper voice is `en_US-lessac-medium`. The corresponding model files are in `voices/`; if they are missing, this script attempts to download them with `curl` (`sudo apt install curl` if needed). The first TTS initialization can take a little while. Make sure `aplay` is installed and that the desired speaker is the default output.

**Audio-loop note:** this is an intermediate teaching step. It uses the earlier, simpler streaming loop, including an unbounded audio queue and a fixed post-answer hush interval. For better handling of audio captured while tools or speech are running, compare it with `voice.py` and especially `needles.py`.

## 6. `needles.py`

**The complete assistant.** This is the most capable example and the best one to explore after the preceding steps. It combines always-on voice input, the “hey needles” wake phrase, tool selection, local shortcuts, and Piper TTS.

### Available capabilities

| What to ask for | How it works |
|---|---|
| Current weather in a city | Open-Meteo geocoding and forecast APIs; no API key required |
| CPU temperature | `vcgencmd` on the Raspberry Pi |
| Free disk space | Space on the root filesystem, reported in decimal gigabytes |
| Available memory | Linux `MemAvailable` from `/proc/meminfo` |
| Exact time | Current local time and date |
| Casual time | Rounded to the nearest five minutes, e.g. “half past one” |
| Dad joke | icanhazdadjoke.com JSON API |
| News headlines | The top five titles from the BBC News RSS feed |
| Coin flip | Local Python random choice |
| Single die / double dice | Local six-sided die rolls |
| Random number | Between 1 and a requested upper limit; spoken number words are supported |
| Help | Fixed description of the available capabilities |

Examples (say the wake phrase first):

- “Hey needles, what’s the weather in Lagos?”
- “Hey needles, exact time.”
- “Hey needles, what time is it?”
- “Hey needles, tell me a joke.”
- “Hey needles, roll one die.”
- “Hey needles, roll two dice.”
- “Hey needles, pick a random number between one and thirty.”
- “Hey needles, what can you do?”

Help, time, and random-number requests have direct local handlers, so they do not need a model tool-selection pass. Other requests go through the Needle agent. `stateless=True` keeps each request independent.

### Audio and speech output

Like `voice.py`, this script captures audio, resamples it when needed, uses a bounded queue, detects the wake phrase across stream steps, and accounts for Whistle’s pending transcript when detecting the end of a request. It pauses capture while tools run and while Piper speaks, then feeds silence to flush the transcription stream. This means the user cannot interrupt a tool call or spoken answer; speech during that time is intentionally discarded.

Piper synthesizes speech locally using the voice files in `voices/`. The script creates that directory and downloads missing model files. Playback goes to the default audio output. To direct it to a paired Bluetooth speaker, inspect the available output IDs and set the speaker as default:

```bash
wpctl status
wpctl set-default <sink-id>
```

## Running and choosing an example

Run a script from this directory with the virtual environment active. Start with `simple.py` and progress in order if you are learning; use `needles.py` if you want the full feature set. You generally should not run multiple voice scripts at once because they compete for the microphone and audio output.

| If you want… | Start with… |
|---|---|
| The smallest possible Needle example | `simple.py` |
| A web API-backed tool | `weather.py` |
| Voice input without a wake word | `voice_simple.py` |
| Always-on listening without spoken output | `voice.py` |
| A small always-on assistant that speaks | `voice_and_tts.py` |
| All tools and voice features together | `needles.py` |

## Troubleshooting

### `vcgencmd` is missing

The CPU-temperature tool is Raspberry Pi-specific. Confirm the command works in a terminal:

```bash
vcgencmd measure_temp
```

### PortAudio or microphone errors

Confirm the microphone is connected and listed as a capture device. Install the mic extra and system library if needed:

```bash
python -m pip install "cactus-needle[mic]"
sudo apt install libportaudio2
arecord -l
```

The voice scripts use the system’s default input device. If multiple devices are connected, check which one is default in your audio settings.

### No sound from TTS

Check that `aplay` is installed, the speaker is connected, and the intended output is selected. On Raspberry Pi OS, `aplay` is provided by `alsa-utils` (`sudo apt install alsa-utils` if needed). For PipeWire, use `wpctl status` and `wpctl set-default <sink-id>`. The `voices/` directory should contain both the `.onnx` model and its `.onnx.json` config file.

### First run takes a while

Needle, Whistle, and Piper may need to download their model or native-engine files. Allow internet access and wait for initialization to finish before speaking.

### Weather, joke, or news requests fail

These capabilities need internet access. Weather and news use Open-Meteo and the BBC RSS feed; jokes use icanhazdadjoke.com. The CPU temperature, disk, memory, time, coin, and dice tools are local.

After model files are downloaded, speech recognition and Piper synthesis run locally. The web-backed tools still send their requests to their respective services—for example, a requested city is sent to Open-Meteo.

## A note on the project’s scope

These scripts are learning examples, not a packaged daemon. They are intentionally direct: tools are visible Python functions, audio capture is in the scripts, and the last example brings the pieces together. A natural next lesson would be to move shared tools and audio code into importable modules, add automated tests, and run the assistant under a service manager.
