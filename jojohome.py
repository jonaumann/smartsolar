import asyncio
import websockets
from aiohttp import web

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
async def test(request):
    return web.Response(text="ok", content_type="text/html")

# Start the servers
async def start_servers():
    # Start the WebSocket server
    async with websockets.serve(websocket_handler, "localhost", 8765):
        print("WebSocket server started.")
        # Start the web server
        app = web.Application()
        app.add_routes([web.get('/', index), web.get('/test', test)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        print("Web server started.")
        # Wait forever
        await asyncio.Future()

asyncio.run(start_servers())
