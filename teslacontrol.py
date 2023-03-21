import requests
import json

with open('tesla token', 'r') as file:
    access_token = file.read()

# Use access token to make requests to Tesla API
vehicle_id = '929722068382371'
charging_amps = 5

# Start charging the vehicle
response1 = requests.post(f'https://owner-api.teslamotors.com/api/1/vehicles/{vehicle_id}/command/set_charging_amps',
    headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
    json={'charging_amps': charging_amps})

response2 = requests.post(f'https://owner-api.teslamotors.com/api/1/vehicles/{vehicle_id}/command/charge_start',
    headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
    json={'charging_amps': charging_amps})

if response1.ok and response2.ok:
    print(f'Charging started at {charging_amps} amps')
else:
    print(f'Error starting charging: {response1.status_code} - {response1.reason}, {response2.status_code} - {response2.reason}')
