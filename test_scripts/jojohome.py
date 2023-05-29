import asyncio
import websockets
from aiohttp import web
from datetime import datetime
import requests
import re

# Define a set to keep track of all connected clients
connected = set()

# Define a callback function to handle incoming messages


async def handle_message(websocket, message):
    print(f"Received message: {message}")
    # Echo the message back to the client
    await websocket.send("message recieved")

# Define a method to send a message to all connected clients


async def send_to_all(message):
    if connected:
        await asyncio.wait([ws.send(message) for ws in connected])

# Define the WebSocket server handler


async def websocket_handler(websocket, path):
    print(f"New connection from {websocket.remote_address}")
    connected.add(websocket)
    try:
        # Keep the connection open to receive incoming messages
        async for message in websocket:
            await handle_message(websocket, message)
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Connection closed by client {websocket.remote_address}")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
    finally:
        connected.remove(websocket)

# Define a web server handler that returns the contents of the index.html file


async def index(request):
    with open("index.html", "r") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")


# Define a web server handler that returns an HTML document with JavaScript code for opening a WebSocket connection


async def log(request):
    with open("log.txt", "r") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/plain")

# Start the servers


def get_solar_power():
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
        return (f"Error fetching web data: {e}")


def check_smart_charge():
    now = datetime.now()
    if now.hour < 4 or now.hour >= 23:
        return ""

    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    power = get_solar_power()

    if power.startswith("Error"):
        return ""

    charge_state = ""

    message = current_time+" "+power+" "+charge_state

    with open("log.txt", "a") as file:
        file.write(message + "\n")

    return message


async def start_servers():
    # Start the WebSocket server
    async with websockets.serve(websocket_handler, "localhost", 4243):
        print("WebSocket server started.")
        # Start the web server
        app = web.Application()
        app.add_routes([web.get('/', index), web.get('/log', log)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 4242)
        await site.start()
        print("Web server started.")
        # Wait forever

        while True:
            await asyncio.sleep(4)
            message = check_smart_charge()
            if message != "":
                await send_to_all(message)


asyncio.run(start_servers())
