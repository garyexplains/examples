# python3 -m venv needle-env
# source needle-env/bin/activate
# pip install "cactus-needle[mic]"
# sudo apt install libportaudio2

import subprocess

import needle
from needle.agent.whistle import record


@needle.tool
def get_cpu_temperature():
    """Return the current CPU temperature of this Raspberry Pi in Celsius."""
    out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)
    return {"temperature_c": float(out.split("=")[1].split("'")[0])}


def main():
    agent = needle.Needle(tools=[get_cpu_temperature], stateless=True)
    print("Push to talk: press Enter to start, then Enter again to stop recording.")

    while True:
        try:
            command = input("\nEnter to record, or q to quit: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if command in {"q", "quit", "exit"}:
            break

        try:
            audio = record()
            transcript = needle.transcribe(
                audio, language="en", keywords=["CPU", "temperature"]
            )["text"].strip()
            if not transcript:
                print("(no speech detected)")
                continue

            print(f"> {transcript}")
            answer = agent.run(transcript)
            print(f"= {answer['results']}")
        except KeyboardInterrupt:
            # record() treats Ctrl-C during capture as a stop-recording action.
            print("\nInterrupted. Enter q at the next prompt to quit.")
        except Exception as error:
            print(f"Voice request failed: {error}")

    print("bye")


if __name__ == "__main__":
    main()
