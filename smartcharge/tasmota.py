import requests


def read_consumed_watts():
    url = "http://192.168.2.216/?m=1"
    try:
        response = requests.get(url)
        power = 0
        if response.ok:
            value = response.text.split("{m}")[2].split(" W{e}")[0]
            power = int(float(value))

        else:
            power = -42
    except Exception as exception:
        power = -1

    return power
