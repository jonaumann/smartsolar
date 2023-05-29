import growattServer
import re

growattServer.GrowattApi.server_url = "https://server.growatt.com/"
api = growattServer.GrowattApi()
login_response = api.login("jonaumann", "jtlr1771")
user_id = login_response['user']['id']
# Get a list of growatt plants.
plant_info = api.plant_info(2012060)
current_power = plant_info["deviceList"][0]["power"]
print(current_power)
