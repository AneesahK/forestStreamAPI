import datetime


this_morning = datetime.datetime(2021, 12, 2, 9, 30)
last_night = datetime.datetime(2009, 12, 1, 20, 0)
print(this_morning.time() < last_night.time())