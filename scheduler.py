import sched
import time
import datetime
import threading

# Time parameter tuple order
HOUR = 0
MINUTE = 1
DURATION = 2

class EventScheduler():    
    def __init__(self):
        self.scheduler_event = None
        self.next_datetime = None
        self.scheduler_object = sched.scheduler(time.time, time.sleep)        

    def set_scheduler(self, scheduler_time, user_callback, user_parameter=None):
        if isinstance(scheduler_time, str):
            scheduler_time = timestr_to_tuple(scheduler_time)
        self.next_datetime = next_datetime_from_time(scheduler_time)
        if not self.scheduler_object.empty() and self.scheduler_event :
            self.scheduler_object.cancel(self.scheduler_event)
        self.scheduler_event = self.scheduler_object.enterabs(self.next_datetime.timestamp(),
                                                              1,
                                                              self.scheduler_callback,
                                                              argument = (user_callback, user_parameter))
        self.scheduler_thread = threading.Thread(target = self.scheduler_object.run)
        self.scheduler_thread.start()
    
    def cancel_scheduler(self):
        if self.scheduler_event:
            self.scheduler_object.cancel(self.scheduler_event)

    def scheduler_callback(self, user_cb, user_param):        
        # Reset the scheduler
        self.set_scheduler((self.next_datetime.hour, self.next_datetime.minute), user_cb, user_param)
        # Execute the user callback with user parameter
        if user_param:
            user_cb(user_param)
        else:
            user_cb()

def next_datetime_from_time(requested_time):
    """ Give the next datetime from requested time """
    if isinstance(requested_time, str):
            requested_time = timestr_to_tuple(requested_time)
    dt_now = datetime.datetime.now()
    dt_updated = dt_now.replace(hour = requested_time[HOUR],
                                minute = requested_time[MINUTE],
                                second = 0,
                                microsecond = 0)
    
    # Check if the datetime is in the future or past
    if (dt_now >= dt_updated):        
        # Result datetime is in the past, adding one day
        dt_updated += datetime.timedelta(days=1)
    
    return dt_updated

def timestr_to_tuple(time_to_convert):
    converted_time = time_to_convert.replace("\"","")
    hour = converted_time.split(':')[HOUR]
    if not (hour == "00" or hour == "0"):
        hour = hour.lstrip('0')
    minute = converted_time.split(':')[MINUTE]
    if not (minute == "00" or minute == "0"):
        minute = minute.lstrip('0')
    return (int(hour), int(minute))