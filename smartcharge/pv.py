import requests

global last_value
if not 'last_value' in globals():
    last_value = 0

# Auslesen PV-Seite


def read_pv_voltage():
    url = "http://192.168.2.254/status.html"
    try:
        response = requests.get(url, auth=('admin', 'admin'))
        response = requests.get(url)
        power = 0
        if response.ok:
            for line in response.text.splitlines():
                if line.strip().startswith("var webdata_now_p"):
                    value = line.split("=")[-1].strip().strip(";").strip("\"")
                    power = int(value)
                    break
        else:
            power = -1
    except Exception as exception:
        power = -1

    return int(power * 7)
