#!/bin/python3
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs
import json
import datetime
import time
import config
import scheduler
import heat_control
from gpiozero import OutputDevice

TIME_FORMAT = "%H:%M"
LIGHT_GPIO = 27
PUMP_GPIO = 22

light = OutputDevice(LIGHT_GPIO)
pump = OutputDevice(PUMP_GPIO)

app_config = config.GrowBoxConfig()
heater = heat_control.HeatControl(app_config.get_day_temperature(),
                                  app_config.get_night_temperature())
w_sched_list = list()
day_scheduler = scheduler.EventScheduler()
night_scheduler = scheduler.EventScheduler()

pump_status = False

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Sending an '200 OK' response
        self.send_response(200)
        # Setting the header
        self.send_header("Content-type", "text/html")
        # Whenever using 'send_header', you also have to call 'end_headers'
        self.end_headers()
        
        config_changed = False

        # Extract query param
        query_components = parse_qs(urlparse(self.path).query)
        if query_components:
            html = json.dumps(query_components)
            # Parse parameters
            
            # Mode (AUTO|FORCED_DAY|FORCED_NIGHT)
            if (config.KEY_MODE in query_components):
                mode = query_components[config.KEY_MODE][0]
                app_config.set_mode(mode)
                config_changed = True

            # Day time
            if (config.KEY_DAY_TIME in query_components):
                day_time = query_components[config.KEY_DAY_TIME][0]
                app_config.set_day_time(test_time(day_time))
                config_changed = True
            
            # Night time
            if (config.KEY_NIGHT_TIME in query_components):
                night_time = query_components[config.KEY_NIGHT_TIME][0]
                app_config.set_night_time(test_time(night_time))
                config_changed = True
            
            # Day temperature
            if (config.KEY_DAY_TEMP in query_components):
                day_temp = query_components[config.KEY_DAY_TEMP][0]
                app_config.set_day_temperature(float(day_temp))
                config_changed = True
            
            # Night temperature
            if (config.KEY_NIGHT_TEMP in query_components):
                night_temp = query_components[config.KEY_NIGHT_TEMP][0]
                app_config.set_night_temperature(float(night_temp))
                config_changed = True
            
            # Waterings
            if (config.KEY_ADD_WATERING in query_components):
                watering_list = query_components[config.KEY_ADD_WATERING]
                for watering in watering_list:
                    app_config.add_watering(watering)
                config_changed = True
            
            if (config.KEY_DEL_WATERING in query_components):
                watering_index = query_components[config.KEY_DEL_WATERING][0]
                app_config.del_watering(watering_index)
                config_changed = True
        
            if config_changed:
                initialize()

        else:
            # Report current parameters here
            html  = "Parameters:<br>"
            html += "Mode: " + app_config.get_mode() + "<br>"
            html += "Day time: " + str(app_config.get_day_time()) + "<br>"
            html += "Night time: " + str(app_config.get_night_time()) + "<br>"
            html += "Day temperature: " + str(app_config.get_day_temperature()) + "<br>"
            html += "Night temperature: " + str(app_config.get_night_temperature()) + "<br>"
            html += "Waterings:<br>"
            if app_config.get_waterings():
                w_idx = 0
                for watering in app_config.get_waterings():
                    html += "Watering " + str(w_idx) + ": " + str(watering) + "<br>"
                    w_idx += 1
            html += "Pump status: " + str(pump_status) + "<br>"
            html += "Temperature: " + str(heater.get_temperature()) + "<br>"
            
        self.wfile.write(bytes(html, "utf8"))
        return

class SimpleServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def test_time(input):
    input = input.replace("\"", "")
    try:
        time.strptime(input, TIME_FORMAT)
        return input
    except ValueError:
        print("WARNING: Invalid time")
        return None

def trigger_watering(duration):
    print("INFO: Trigger watering for", duration, "seconds...")
    pump.on()
    pump_status = True
    time.sleep(duration)
    pump.off()
    pump_status = False
    print("INFO: End of watering")

def trigger_day_mode():
    print("INFO: Trigger day mode at",
          datetime.datetime.now().strftime("%H:%M:%S"))
    heater.set_day_mode()
    light.on()

def trigger_night_mode():
    print("INFO: Trigger night mode",
          datetime.datetime.now().strftime("%H:%M:%S"))
    heater.set_night_mode()
    light.off()

def initialize():
    # Apply current mode from configuration
    if app_config.get_mode() == config.MODE_FORCE_DAY:
        print("INFO: Day mode forced")
        trigger_day_mode()
    elif app_config.get_mode() == config.MODE_FORCE_NIGHT:
        print("INFO: Night mode forced")
        trigger_night_mode()
    elif app_config.get_mode() == config.MODE_AUTO:
        print("INFO: Mode auto")
        if app_config.get_day_time and app_config.get_night_time:            
            print("INFO: Configure scheduler from configuration")
            day_scheduler.cancel_scheduler()
            night_scheduler.cancel_scheduler()
            config_day_str = str(app_config.get_day_time())
            config_night_str = str(app_config.get_night_time())
            day_scheduler.set_scheduler(config_day_str, trigger_day_mode)
            night_scheduler.set_scheduler(config_night_str, trigger_night_mode)
            
            # Determine if it's day or night
            current_time_str = str(datetime.datetime.now().hour) + \
                               ":" + \
                               str(datetime.datetime.now().minute)
            if time.strptime(current_time_str, TIME_FORMAT) < time.strptime(config_night_str, TIME_FORMAT):
                trigger_day_mode()
            else:
                trigger_night_mode()
        else:
            print("WARNING: No valid day and night times, force day mode")
            trigger_day_mode()

        # Retreiving waterings from configuration
        if app_config.get_waterings():
            # Cancel schedulers if exists
            if len(w_sched_list):
                for w_sched in w_sched_list:
                    w_sched.cancel_scheduler()
                w_sched_list.clear()

            for watering in app_config.get_waterings():
                watering_tuple = tuple(eval(watering))                    
                watering_sched = scheduler.EventScheduler()
                watering_sched.set_scheduler(watering_tuple, trigger_watering, watering_tuple[scheduler.DURATION])
                w_sched_list.append(watering_sched)

        # Heater
        heater.set_day_temperature(app_config.get_day_temperature())
        heater.set_night_temperature(app_config.get_night_temperature())
        

if __name__ == "__main__":    
    initialize()
    address = ('', 8000)
    my_server = SimpleServer(address, MyHttpRequestHandler)
    my_server.serve_forever()