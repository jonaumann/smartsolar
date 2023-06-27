################################################################################################################################
# PV-Leistungs abhängiges Laden Tesla über https://github.com/tdorssers/TeslaPy.
# Token muss bereis in cache.json vorhanden sein
# Das Log-File ist über <IP-Adresse>:8000 aufrufbar
# <IP-Adresse>:8000/?quit=true beendet das Program
# TODO: Benutzeroberfläche zum starten/stoppen und Einstellung verschiedener Parameter
# TODO: Auto Refresh der Benutzeroberfläche / Log Ausgaben
################################################################################################################################
import sys
import os
import logging
import http.server
import socketserver
import threading
import socket
import argparse
import geopy.geocoders
import urllib
import time
import constants_pv_charging
import time
import datetime


from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from teslapy import Tesla
from urllib.parse import urlsplit, parse_qs
from http import HTTPStatus
from pv import read_pv_voltage
from tasmota import read_consumed_watts
from Hue import Hue

oldhtml = ""
charge_level = 0

hue = Hue()
# hue.list_lights()

###############################################################################################################
# Main
###############################################################################################################


def main():
    # Threaded Http Server initialisiern
    httpd = http.server.ThreadingHTTPServer(
        ("", constants_pv_charging.SERVER_PORT), HttpHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    global charge_level
    charge_level = 0

    ampere = 3
    last_ampere = 0
    consumed = 0
    state = ""

    # Endlosschleife
    while True:
        try:
            current_time = datetime.datetime.now().time()
            with open("info.log", "w") as file:
                # Truncate the file
                file.truncate()
            log(time.ctime(time.time()))
            # pv_voltage = read_pv_voltage()
            # log('current pv watts: ' + str(pv_voltage))
            consumed = read_consumed_watts()
            log('current consumed watts: ' + str(consumed))

            if consumed > 0:
                hue.switch_light(3, False)
                if consumed > 2000:
                    ampere -= 3
                elif consumed > 1000:
                    ampere -= 2
                elif consumed > 200:
                    ampere -= 1
                if ampere < 1:
                    ampere = 1

            else:
                ampere += 1
                if ampere > 5:
                    ampere = 5

                hue.switch_light(3, True)
                # int(hue.convert_to_percent(pv_voltage, 300, 4500))
                brightness = 50
                if brightness == 0:
                    brightness = 1
                log('setting brightness to ' + str(brightness))
                hue.set_light_brightness(3, brightness)

            log('current ampere: ' + str(ampere))
            if ampere != last_ampere or state != 'ready for charging':
                state = tesla_pv_charge_control(ampere)
                log('state: ' + str(state))
                if ampere != last_ampere:
                    log('changing ampere to ' + str(ampere))
                    last_ampere = ampere

            else:
                log("doing nothing")

        except Exception as exception:
            log(str(exception))
            try:
                hue.switch_light(3, False)
            except Exception as ex:
                log(str(ex))

        log("###")

        time.sleep(constants_pv_charging.SLEEP_BETWEEN_CALLS)


###############################################################################################################
# Tesla Ampere Einstellen in Abhängigkeit der PV-Leistung
###############################################################################################################
def tesla_pv_charge_control(ampere):

    with Tesla("jochen.naumann@strelen.de", False, False) as tesla:
        # Token muss in cache.json vorhanden sein. Vorher einfach z.B. gui.py aufrufen und 1x einloggen
        tesla.fetch_token()
        vehicles = tesla.vehicle_list()

        # Auto schläft, kann nicht geladen werden
        if vehicles[0]['state'] != "online":
            log('Sleeping, trying to wake up')
            vehicles[0].sync_wake_up()

        # Status ausgeben
        log('Tesla Current Ampere: ' + str(vehicles[0].get_vehicle_data()['charge_state']['charge_current_request'])
            + '\n Charge Status: ' +
            str(vehicles[0].get_vehicle_data()[
                'charge_state']['charging_state'])
            + '\n Battery Lvl: ' +
            str(vehicles[0].get_vehicle_data()[
                'charge_state']['battery_level'])
            )

        # Auto nicht angesteckt, kann nicht geladen werden
        if vehicles[0].get_vehicle_data()['charge_state']['charging_state'] == 'Disconnected':
            log('Charger disconnected, can not set charge!')
            tesla_set_charge_level(vehicles, 50)
            return "disconnected"
        # Auto angesteckt
        else:
            # Ist das Auto zu Hause?
            coords = '%s, %s' % (round(vehicles[0].get_vehicle_data()[
                'drive_state']['latitude'], 2), round(vehicles[0].get_vehicle_data()['drive_state']['longitude'], 1))

            if coords != constants_pv_charging.HOME_LOCATION:
                log('Vehicle not at home. Doing nothing')
                return 'not home'

            # > 1 Ampere -> Laden
            if ampere > constants_pv_charging.MINIMUM_AMPERE_LEVEL:

                if vehicles[0].get_vehicle_data()['charge_state']['charge_current_request'] != ampere:
                    vehicles[0].command(
                        'CHARGING_AMPS', charging_amps=ampere)
                    # Wenn unter 5 Ampere, muss der Wert 2x gesetzt werden
                    if ampere < 5:
                        vehicles[0].command(
                            'CHARGING_AMPS', charging_amps=ampere)

                log('Tesla Charge Ampere: ' + str(ampere))
                tesla_set_charge_level(vehicles, 100)
            # <= 1 Ampere -> Lohnt sich nicht (ca. 300 W Grundlast), laden stoppen
            else:
                tesla_set_charge_level(vehicles, 50)
                vehicles[0].command(
                    'CHARGING_AMPS', charging_amps=1)
                # Wenn unter 5 Ampere, muss der Wert 2x gesetzt werden
                vehicles[0].command(
                    'CHARGING_AMPS', charging_amps=1)
                # log("sleeping after stopcharge " +
                #    str(constants_pv_charging.WAIT_SECONDS_AFTER_CHARGE_STOP))
                time.sleep(
                    constants_pv_charging.WAIT_SECONDS_AFTER_CHARGE_STOP)
        return 'ready for charging'


def tesla_set_charge_level(vehicles, limit):
    global charge_level
    if charge_level == limit:
        return
    charge_level = limit

    try:
        if vehicles[0]['state'] != "online":
            log('Sleeping, trying to wake up')
            vehicles[0].sync_wake_up()
            log("woken up")

        if vehicles[0].command("CHANGE_CHARGE_LIMIT", percent=limit):
            log("charging limit set to "+str(limit))

    except Exception as ex:
        log("error setting charge limit: "+str(ex))


###############################################################################################################
# Http-Handler, gibt das Log-File zurück. Parameter quit beendet das Programm
###############################################################################################################


class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):

        query = urlsplit(self.path).query
        params = parse_qs(query)
        # Program beenden, falls Parameter quit übergeben wurde
        if "quit" in params:
            log('User Exit')
            os._exit(0)
        elif "m" in params:
            info = b""
            while ("###" not in info.decode('utf-8')):
                logFile = open("info.log", "rb")
                info = logFile.read()
                print(info)
                time.sleep(1)

            self.send_response(HTTPStatus.OK)
            self.end_headers()
            self.wfile.write(info)
        elif self.path == "/":
            file = open("index.html", "rb")
            html = file.read()
            self.send_response(HTTPStatus.OK)
            self.end_headers()
            self.wfile.write(html)
        else:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()


def log(text):
    with open("info.log", "a") as file:
        # Write the text to the file
        file.write(text + "\n")


if __name__ == "__main__":
    main()
