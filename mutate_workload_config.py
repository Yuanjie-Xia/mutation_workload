import pandas as pd
import math
from time import ctime, localtime, sleep
from datetime import date, timedelta
import re


class workload:
    def __init__(self, time_window_length, system, ):
        self.time_window_length = time_window_length
        self.system = system