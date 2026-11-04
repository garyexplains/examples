# python3 -m venv needle-env
# source needle-env/bin/activate
# pip install "cactus-needle[mic]"
# sudo apt install libportaudio2
import re
import subprocess

import needle

@needle.tool
def get_cpu_temperature():

    """Return the current CPU temperature of this Raspberry Pi in Celsius."""

    out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)

    return {"temperature_c": float(out.split("=")[1].split("'")[0])}



SAMPLE_RATE = 16000          # what Whistle wants
ACTIVATION = "hey needles"   # wake word; spoken e.g. "hey needles, what's the CPU temperature"
WAKE_KEYWORDS = ["hey needles", "temperature", "CPU"]
SILENCE_SECONDS = 1.8        # how long the command may trail off before it runs
WAKE_BUFFER_SECONDS = 2.0    # retain partial wake-word text across stream steps
_ACTIVATION_PATTERN = r"[\W_]+".join(re.escape(word) for word in ACTIVATION.split())
ACTIVATION_RE = re.compile(r"(?<!\w)" + _ACTIVATION_PATTERN + r"(?!\w)", re.IGNORECASE)


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


def mic_loop(agent):
    """Always-on: stream the mic through Whistle, gate on the wake word,
    and run everything said after it as an agent query."""
    import numpy
    import queue
    import sounddevice
    import soxr
    import threading

    # Keep a bounded amount of audio; stale speech is worse than a brief drop.
    heard = queue.Queue(maxsize=64)
    native = int(sounddevice.query_devices(kind="input")["default_samplerate"])
    resampler = None if native == SAMPLE_RATE else soxr.ResampleStream(
        native, SAMPLE_RATE, 1, dtype="float32", quality="HQ")
    capture_lock = threading.Lock()
    capture_state = {"busy": False, "generation": 0}
    audio_problem = threading.Event()

    def capture(samples, frames, time_info, status):
        if status:
            audio_problem.set()
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
                # Drop old buffered audio and restart from the newest callback block.
                capture_state["generation"] += 1
                generation = capture_state["generation"]
                while True:
                    try:
                        heard.get_nowait()
                    except queue.Empty:
                        break
                heard.put_nowait((generation, audio))
                audio_problem.set()

    def chunks():
        block, held, generation = [], 0, None
        while True:
            next_generation, data = heard.get()
            if next_generation != generation:
                # Do not join audio recorded before a busy period to new audio.
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
            # Silence advances Whistle past any pending tail from the prior turn.
            silence = numpy.zeros(SAMPLE_RATE, dtype=numpy.float32)
            heard.put_nowait((generation, silence))
            heard.put_nowait((generation, silence.copy()))
            capture_state["busy"] = False

    def answer_command(spoken):
        """Run one query while discarding mic audio until the tool call is done."""
        pause_capture()
        try:
            print(f"> {spoken}")
            try:
                answer = agent.run(spoken)
            except Exception as error:
                print(f"  agent error: {error}", flush=True)
            else:
                print(f"= {answer['results']}", flush=True)
        finally:
            resume_capture()

    armed, command, quiet, received = False, "", 0.0, 0.0
    wake_buffer, wake_idle = "", 0.0
    with sounddevice.InputStream(samplerate=native, channels=1,
                                 dtype="float32", callback=capture):
        print(f'● always-on: say "{ACTIVATION}, ..." — Ctrl-C to quit '
              "(mic pauses while tools run)", flush=True)
        for step in needle.stream(chunks(), language="en", keywords=WAKE_KEYWORDS):
            text = (step.get("text") or "").strip()
            pending = (step.get("pending") or "").strip()
            spoken_seconds = max(0.0, step["received"] - received)
            received = step["received"]

            if audio_problem.is_set():
                print("  warning: audio callback/queue overflow; some input was dropped",
                      flush=True)
                audio_problem.clear()

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
            # Empty committed text may still have an unconfirmed speech tail.
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


if __name__ == "__main__":
    try:
        agent = needle.Needle(tools=[get_cpu_temperature], stateless=True)
        mic_loop(agent)
    except KeyboardInterrupt:
        print("\nbye")
