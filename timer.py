# -*- coding: utf-8 -*-

import datetime

class Timer:
    """
    A simple timer class.
    """
    def __init__(self):
        """
        Initializes a new instance of the Timer class.
        """
        self.start_time = None
        self.end_time = None
        
    def reset(self):
        """
        Resets the timer.
        """
        self.start_time = None
        self.end_time = None

    def start(self):
        """
        Starts the timer.
        """
        if self.start_time is not None:
            raise Exception("Timer is already running. Please stop the timer before starting it again.")
        self.start_time = datetime.datetime.now()

    def stop(self):
        """
        Stops the timer.
        """
        if self.start_time is None:
            raise Exception("Timer is not running. Please start the timer before stopping it.")
        self.end_time = datetime.datetime.now()

    def elapsed_time(self):
        """
        Returns the elapsed time since the timer was started.
        """
        if self.start_time is None or self.end_time is None:
            raise Exception("Cannot calculate elapsed time. Make sure the timer has been started and stopped.")
        else:
            elapsed_time = self.end_time - self.start_time
            
            # Format elapsed_time as HH:MM:SS
            hours, remainder = divmod(elapsed_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_time = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)
            self.start_time = None
            self.end_time = None
            return formatted_time
