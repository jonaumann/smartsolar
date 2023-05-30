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


from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from teslapy import Tesla
from urllib.parse import urlsplit, parse_qs
from http import HTTPStatus
from pv import read_pv_voltage
from Hue import Hue
from mylogger import *

hue = Hue()
# hue.list_lights()

###############################################################################################################
# Main
###############################################################################################################


def main():
    # Log intitlisieren
    setuplog()

    # Threaded Http Server initialisiern
    httpd = http.server.ThreadingHTTPServer(
        ("", constants_pv_charging.SERVER_PORT), HttpHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()

    # Endlosschleife Aufruf pv_charge_control mit 10 Sekunden Pause
    while True:
        try:
            tesla_pv_charge_control()

        except Exception as exception:
            log(exception)
            try:
                hue.switch_light(3, False)
            except Exception as ex:
                log(ex)

        time.sleep(constants_pv_charging.SLEEP_BETWEEN_CALLS)

###############################################################################################################
# Logging-Einstellungen
###############################################################################################################


###############################################################################################################
# Tesla Ampere Einstellen in Abhängigkeit der PV-Leistung
###############################################################################################################
def tesla_pv_charge_control():
    with Tesla("jochen.naumann@strelen.de", False, False) as tesla:
        # Token muss in cache.json vorhanden sein. Vorher einfach z.B. gui.py aufrufen und 1x einloggen
        tesla.fetch_token()
        vehicles = tesla.vehicle_list()

        # Auto schläft, kann nicht geladen werden
        if vehicles[0]['state'] != "online":
            log('Sleeping, trying to wake up')
            vehicles[0].sync_wake_up()
            return
        # Auto wach
        else:
            # Status ausgeben
            log('Online Current Ampere: ' + str(vehicles[0].get_vehicle_data()['charge_state']['charge_current_request'])
                + ', Charge Limit: ' +
                str(vehicles[0].get_vehicle_data()[
                    'charge_state']['charge_limit_soc'])
                + ', Charge Status: ' +
                str(vehicles[0].get_vehicle_data()[
                    'charge_state']['charging_state'])
                + ', Battery Lvl: ' +
                str(vehicles[0].get_vehicle_data()[
                    'charge_state']['battery_level'])
                )

            pv_voltage = read_pv_voltage()

            if pv_voltage < 300:
                hue.switch_light(3, False)
            else:
                hue.switch_light(3, True)
                brightness = int(
                    hue.convert_to_percent(pv_voltage, 300, 4500))
                if brightness == 0:
                    brightness = 1
                log('setting brightness to ' + str(brightness))
                hue.set_light_brightness(3, brightness)

            kilowatts = pv_voltage/1000
            # ampere = kilowatts*constants_pv_charging.AMPERE_FACTOR;
            ampere_rounded = round(
                kilowatts*constants_pv_charging.AMPERE_FACTOR)
            if kilowatts < 1.5:
                # Unter 1,5 nicht mehr laden
                ampere_rounded = 1

            log('Kilowatt PV-Anlage: ' + str(kilowatts) + ' -> Ampere Roundend: ' +
                str(ampere_rounded) + ', Approx KW:' + str(ampere_rounded*(11/16)))

            # Auto nicht angesteckt, kann nicht geladen werden
            if vehicles[0].get_vehicle_data()['charge_state']['charging_state'] == 'Disconnected':
                log('Charger disconnected, can not set charge!')
                return
            # Auto angesteckt
            else:
                # Ist das Auto zu Hause?
                # coords = '%s, %s' % (vehicles[0].get_vehicle_data()[
                #                     'drive_state']['latitude'], vehicles[0].get_vehicle_data()['drive_state']['longitude'])
                # osm = Nominatim(user_agent='TeslaPy')
                # location = osm.reverse(coords).address
                # if location in constants_pv_charging.HOME_LOCATION:
                #    log('Vehicle not at home. Doing nothing')
                #    return
                # Hier wird über ein Modul die aktuelle Leistung der PV-Anlage ausgelesen.

                # > 1 Ampere -> Laden
                if ampere_rounded > constants_pv_charging.MINIMUM_AMPERE_LEVEL:
                    # Wenn nicht lädt, laden starten, außer wenn schon complete
                    if vehicles[0].get_vehicle_data()['charge_state']['charging_state'] != 'Charging' and vehicles[0].get_vehicle_data()['charge_state']['charging_state'] != 'Complete':
                        vehicles[0].command('START_CHARGE')
                        print('start charging')
                    # Charging Amps in Abhängigkeit PV-Leistung setzen
                    if vehicles[0].get_vehicle_data()['charge_state']['charge_current_request'] != ampere_rounded:
                        vehicles[0].command(
                            'CHARGING_AMPS', charging_amps=ampere_rounded)
                        # Wenn unter 5 Ampere, muss der Wert 2x gesetzt werden
                        if ampere_rounded < 5:
                            vehicles[0].command(
                                'CHARGING_AMPS', charging_amps=ampere_rounded)
                        log('Setting Ampere: ' + str(ampere_rounded))
                    else:
                        log('Did not change. Not Setting a value')
                # <= 1 Ampere -> Lohnt sich nicht (ca. 300 W Grundlast), laden stoppen und etwas warten, damit nicht ständig das Laden gestart und gestoppt wird
                else:
                    if vehicles[0].get_vehicle_data()['charge_state']['charging_state'] == 'Charging':
                        log("stop charging")
                        vehicles[0].command('STOP_CHARGE')
                        vehicles[0].command(
                            'CHARGING_AMPS', 1)
                        # Wenn unter 5 Ampere, muss der Wert 2x gesetzt werden
                        vehicles[0].command(
                            'CHARGING_AMPS', 1)
                    log("sleeping after stopcharge " +
                        str(constants_pv_charging.WAIT_SECONDS_AFTER_CHARGE_STOP))
                    time.sleep(
                        constants_pv_charging.WAIT_SECONDS_AFTER_CHARGE_STOP)
        print('')


###############################################################################################################
# Http-Handler, gibt das Log-File zurück. Parameter quit beendet das Programm
###############################################################################################################
class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        logFile = open(constants_pv_charging.LOG_FILE_NAME, "rb")
        # Ausgabe des Log-Files
        self.wfile.write(logFile.read())

        query = urlsplit(self.path).query
        params = parse_qs(query)
        # Program beenden, falls Parameter quit übergeben wurde
        if "quit" in params:
            log('User Exit')
            os._exit(0)


if __name__ == "__main__":
    main()
