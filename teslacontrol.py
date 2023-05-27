import requests
import json

with open('tesla_refresh_token', 'r') as file:
    refresh_token = file.read()


response = requests.post(
    "https://owner-api.teslamotors.com/oauth/token",
    data={
        "grant_type": "password",
        "email": "jochen.naumann@strelen.de",
        "password": "Robert5Bosch",
        "client_secret": "c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3",
        "client_id": "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
    },
)

# Extract the new access token from the response
access_token = response.json()["access_token"]

# with open('tesla token', 'r') as file:
#    access_token = file.read()

# Use access token to make requests to Tesla API
vehicle_id = '929722068382371'
charging_amps = 5

# Start charging the vehicle
response1 = requests.post(f'https://owner-api.teslamotors.com/api/1/vehicles/{vehicle_id}/command/set_charging_amps',
                          headers={'Authorization': f'Bearer {access_token}',
                                   'Content-Type': 'application/json'},
                          json={'charging_amps': charging_amps})

response2 = requests.post(f'https://owner-api.teslamotors.com/api/1/vehicles/{vehicle_id}/command/charge_stop',
                          headers={'Authorization': f'Bearer {access_token}',
                                   'Content-Type': 'application/json'},
                          json={'charging_amps': charging_amps})

if response1.ok and response2.ok:
    print(f'Charging started at {charging_amps} amps')
else:
    print(
        f'Error starting charging: {response1.status_code} - {response1.reason}, {response2.status_code} - {response2.reason}')
