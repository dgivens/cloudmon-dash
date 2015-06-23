import pytz
from cloudmon_dash import app, mongo
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from pytz import timezone


def get_alarms(state=None):
    alerting = []
    if state:
        search = {'state': state}
    else:
        search = {'state': {'$ne': 'OK'}}

    cursor = mongo.db.alarms.find(search)

    for alarm in cursor.sort('details.timestamp', DESCENDING):
        alerting.append(alarm)
    return alerting


def get_events(skip=0, limit=10):
    events = []
    cursor = mongo.db.notifications.find()
    for event in cursor.sort('details.timestamp', DESCENDING).skip(skip).limit(limit):
        event_ts = event['details']['timestamp']
        local_tz = app.config['TIME_ZONE']
        local_dt = utc_timestamp_to_local(event_ts, local_tz)
        event['details']['timestamp'] = local_dt.strftime('%d %b %Y %H:%M:%S %Z')
        event['details']['state_label'] = get_state_label(event['details']['state'])
        events.append(event)
    return events


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


def get_state_label(state):
    if state == 'OK':
        return 'success'
    elif state == 'WARNING':
        return 'warning'
    else:
        return 'danger'
