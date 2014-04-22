import pytz
from datetime import datetime
from cloudmon_dash import app, mongo
from pytz import timezone


def get_alarms(state=None):
    alerting = []
    if state:
        search = {'state': state}
    else:
        search = {'state': {'$ne': 'OK'}}

    for alarm in mongo.db.alarms.find(search):
        alerting.append(alarm)
    return alerting


def update_alarm(hostname, check_label, alarm_label, **kwargs):
    alarm = mongo.db.alarms.find_one({'hostname': hostname,
                                     'check': check_label,
                                     'alarm': alarm_label})
    if alarm is None:
        alarm = {}
    alarm['hostname'] = hostname
    alarm['check'] = check_label
    alarm['alarm'] = alarm_label
    for key, value in kwargs.iteritems():
        alarm[key] = value
    mongo.db.alarms.save(alarm)
    return alarm


def utc_timestamp_to_local(utc_ts, local_tz):
    utc = pytz.utc
    utc_dt = datetime.utcfromtimestamp(utc_ts / 1000).replace(tzinfo=utc)
    local_tz = timezone(local_tz)
    return local_tz.normalize(utc_dt.astimezone(local_tz))
