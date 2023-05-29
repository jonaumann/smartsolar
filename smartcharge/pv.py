import growattServer
import re

global last_value
if not 'last_value' in globals():
    last_value = 0

# Auslesen PV-Seite


def read_pv_voltage():
    growattServer.GrowattApi.server_url = "https://server.growatt.com/"
    api = growattServer.GrowattApi()
    login_response = api.login("jonaumann", "Jesus2010")
    user_id = login_response['user']['id']
    # Get a list of growatt plants.
    plant_info = api.plant_info(2012060)
    current_power = plant_info["deviceList"][0]["power"]
    return int(float(current_power))
