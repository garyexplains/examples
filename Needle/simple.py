# python3 -m venv needle-env
# source needle-env/bin/activate
# pip install cactus-needle
import needle
import subprocess

@needle.tool
def get_temperature():

    """Return the current CPU temperature of this Raspberry Pi in Celsius."""

    out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)

    return {"temperature_c": float(out.split("=")[1].split("'")[0])}



agent = needle.Needle(tools=[get_temperature])
print(agent.run("How hot is this Raspberry Pi??")["results"])
