import json

CONFIG_FILENAME = "/home/pi/growbox/conf.json"
MODE_AUTO = "AUTO"
MODE_FORCE_DAY = "DAY FORCED"
MODE_FORCE_NIGHT = "NIGHT FORCED"
DEFAULT_MODE = MODE_FORCE_DAY
DEFAULT_TEMP = 20

KEY_DAY_TIME = "day_time"
KEY_NIGHT_TIME = "night_time"
KEY_DAY_TEMP = "day_temp"
KEY_NIGHT_TEMP = "night_temp"
KEY_MODE = "mode"
KEY_WATERINGS = "waterings"
KEY_ADD_WATERING = "add_watering"
KEY_DEL_WATERING = "del_watering"
KEY_GET_WATERINGS = "get_waterings"

class GrowBoxConfig():
    def __init__(self):
        self.config_dict = dict()
        try:
            config_file = open(CONFIG_FILENAME, "rt")
            self.config_dict = json.load(config_file)
        except:
            print("ERROR: Unable to open or parse", CONFIG_FILENAME, "- beginning new configuration")
            self.set_mode(DEFAULT_MODE)
            self.set_day_temperature(DEFAULT_TEMP)
            self.set_night_temperature(DEFAULT_TEMP)
            self.config_dict[KEY_WATERINGS] = list()

    def save_config_file(self):
        try:
            config_file = open(CONFIG_FILENAME, "wt")
            config_file.write(json.dumps(self.config_dict))            
        except:
            print("ERROR: Could not write to config file")
        else:
            config_file.close()

    def get_day_time(self):
        return self.config_dict.get(KEY_DAY_TIME)

    def set_day_time(self, day_time):
        self.config_dict[KEY_DAY_TIME] = day_time
        self.save_config_file()

    def get_night_time(self):
        return self.config_dict.get(KEY_NIGHT_TIME)

    def set_night_time(self, night_time):
        self.config_dict[KEY_NIGHT_TIME] = night_time
        self.save_config_file()

    def get_day_temperature(self):
        return self.config_dict.get(KEY_DAY_TEMP)
        
    def set_day_temperature(self, day_temperature):
        self.config_dict[KEY_DAY_TEMP] = day_temperature
        self.save_config_file()

    def get_night_temperature(self):
        return self.config_dict.get(KEY_NIGHT_TEMP)

    def set_night_temperature(self, night_temperature):
        self.config_dict[KEY_NIGHT_TEMP] = night_temperature
        self.save_config_file()

    def get_mode(self):
        return self.config_dict.get(KEY_MODE)

    def set_mode(self, mode):
        if mode == MODE_FORCE_DAY or mode == MODE_FORCE_NIGHT or mode == MODE_AUTO :
            self.config_dict[KEY_MODE] = mode
            self.save_config_file()
        else:
            print("WARNING : Unknown mode")

    def get_waterings(self):
        return self.config_dict.get(KEY_WATERINGS)

    def add_watering(self, watering):
        self.config_dict[KEY_WATERINGS].append(watering)
        self.save_config_file()

    def del_watering(self, index):
        try:
            self.config_dict[KEY_WATERINGS].pop(int(index))
        except:
            print("WARNING: Trying to delete bad index watering")
        else:
            self.save_config_file()
