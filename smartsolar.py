import asyncio
import websockets
import requests
from aiohttp import web
import re

charging_amps = 5
access_token = ""


async def handle(request):
    return web.Response(text=get_inverter_data())


def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    print("starting web server")
    web.run_app(app)


def get_inverter_data():
    try:
        url = "http://192.168.2.195/status.html"
        response = requests.get(url, auth=('admin', 'admin'))
        response.raise_for_status()  # Raise an exception if the HTTP request fails
        # Extract the value of webdata_now_p from the response text using regex
        match = re.search(
            r"var webdata_now_p = \"(\d+)\"", response.text)
        if match:
            webdata_now_p = match.group(1)
            return webdata_now_p
        else:
            raise ValueError(
                "webdata_p_now variable not found in response text")
    except Exception as e:
        print(f"Error fetching web data: {e}")
        raise e


def start_charging():
    # Start charging the vehicle
    response1 = requests.post(f'https://owner-api.teslamotors.com/api/1/vehicles/{vehicle_id}/command/set_charging_amps',
                              headers={
                                  'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
                              json={'charging_amps': charging_amps})

    response2 = requests.post(f'https://owner-api.teslamotors.com/api/1/vehicles/{vehicle_id}/command/charge_start',
                              headers={
                                  'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
                              json={'charging_amps': charging_amps})

    if response1.ok and response2.ok:
        print(f'Charging started at {charging_amps} amps')
    else:
        print(
            f'Error starting charging: {response1.status_code} - {response1.reason}, {response2.status_code} - {response2.reason}')


if __name__ == '__main__':

    start_web_server()
