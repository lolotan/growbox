import threading
import time
from gpiozero import OutputDevice

HYSTERESIS = 1.0
SENSOR_PATH = "/sys/bus/w1/devices/28-3c01d075a3e6/temperature"
HEATER_GPIO = 23
PERIOD = 0.5

class HeatControl():    
    def __init__(self, day_temp, night_temp):
        self.set_day_temperature(day_temp)
        self.set_night_temperature(night_temp)
        self.set_temperature = self.day_temperature
        self.hc_thread = threading.Thread(target = self.heat_control_loop)
        self.hc_thread.start()
        self.heater = OutputDevice(HEATER_GPIO)

    def set_day_temperature(self, day_temp):
        self.day_temperature = day_temp

    def set_night_temperature(self, night_temp):
        self.night_temperature = night_temp

    def set_day_mode(self):
        self.set_temperature = self.day_temperature

    def set_night_mode(self):
        self.set_temperature = self.night_temperature

    def get_temperature(self):
        sensor_file = open(SENSOR_PATH, "r")
        temperature = round(float(sensor_file.read()) / 1000.0, 1)
        sensor_file.close()
        return temperature

    def heat_control_loop(self):
        while True:
            read_temperature = self.get_temperature()
            if  read_temperature > (self.set_temperature + HYSTERESIS):                
                self.heater.off()

            elif read_temperature < (self.set_temperature - HYSTERESIS):
                self.heater.on()

            time.sleep(PERIOD)