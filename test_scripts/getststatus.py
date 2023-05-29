import requests

# Define URL
url = "http://192.168.2.195/status.html"

response = requests.get(url, auth=('admin', 'admin'))
response = requests.get(url)

if response.ok:
    for line in response.text.splitlines():
        if line.strip().startswith("var webdata_now_p"):
            value = line.split("=")[-1].strip().strip(";").strip("\"")
            print(value)
            break
else:
    print("Failed to fetch inverter status!")
