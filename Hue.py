import requests
import json

class Hue:
    api_key = 'IXlMETLE48E83QI1Rwz-TOHkQu-xa7gXnN7wNr4k'
    bridge_ip = '192.168.2.100'

    def execute_hue_command(self, command, payload=None):
        """
        Executes a Philips Hue API command with the given API key, command, and payload (if provided).
        Returns the response from the API as a dictionary.
        """
        url = f'http://{self.bridge_ip}/api/{self.api_key}/{command}'
        response = None

        if payload is not None:
            response = requests.put(url, data=json.dumps(payload))
        else:
            response = requests.get(url)

        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                print("Response is not valid JSON:")
                print(response.content)
                return None
        else:
            return None

    def list_lights(self):
        response = self.execute_hue_command('lights')
        print(f"Found {len(response)} lights:")
        for light_id, light_info in response.items():
            print(f"Light {light_id}: {light_info['name']}")

    def switch_light(self, light_id, state=True):
        payload = {"on": state}
        response = self.execute_hue_command(f'lights/{light_id}/state', payload)
        if response is not None:
            print("Light turned on successfully")
        else:
            print("Failed to turn on the light")

    def set_light_brightness(self, light_id, brightness):
        """
        Sets the brightness of a Philips Hue light with the given API key, light ID, and brightness value.
        Returns True if the brightness was set successfully, False otherwise.
        """
        # Construct the payload with the desired brightness value
        payload = {"bri": brightness}

        # Send the API command to set the light state
        response = self.execute_hue_command(f'lights/{light_id}/state', payload)

        # Check if the brightness was set successfully
        if response is not None and "success" in response[0]:
            print("Brightness set successfully")
        else:
            print('Failed to set brightness')

    def set_light_color(self, light_id, hue, saturation):
        """
        Sets the color of a Philips Hue light with the given API key, light ID, hue value, and saturation value.
        Returns True if the color was set successfully, False otherwise.
        """
        # Construct the payload with the desired color values
        payload = {"hue": hue, "sat": saturation}

        # Send the API command to set the light state
        response = self.execute_hue_command(f'lights/{light_id}/state', payload=payload)

        # Check if the color was set successfully
        if response is not None and "success" in response[0]:
            print("Color set successfully")
        else:
            print('Failed to set color')


def main():
    # Initialize the Hue object
    hue = Hue()

    # Call the methods on the Hue object
    hue.list_lights()
    hue.switch_light(3, True)
    hue.set_light_brightness(3, 100)

if __name__ == '__main__':
    main()
