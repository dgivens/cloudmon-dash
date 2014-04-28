import json
import pytz
from bson import json_util
from bson.objectid import ObjectId
from datetime import datetime
from flask import redirect, render_template, request, url_for
from cloudmon_dash import app, mongo
from cloudmon_dash.utils import get_alarms, get_events, update_alarm
from cloudmon_dash.utils import utc_timestamp_to_local
from pymongo import ASCENDING, DESCENDING
from sets import Set


@app.route('/')
def index():
    alarms = get_alarms()
    events = get_events(skip=0, limit=10)
    return render_template('index.html', alarms=alarms, events=events)


@app.route('/hosts')
def hosts():
    hosts = Set()
    for alarm in mongo.db.alarms.find():
        hosts.add(alarm['hostname'])
    return render_template('hosts.html', hosts=hosts)


@app.route('/history/<hostname>')
def history(hostname):
    events = []
    cursor = mongo.db.notifications.find({'entity.label': hostname})
    total = cursor.count()
    pages = (total + (-total % 25)) // 25
    page = int(request.args.get('page')) if request.args.get('page') else 1
    skip = (page - 1) * 24
    limit = page * 24
    for event in cursor.sort('details.timestamp', DESCENDING).skip(skip).limit(limit):
        event_ts = event['details']['timestamp']
        local_tz = app.config['TIME_ZONE']
        local_dt = utc_timestamp_to_local(event_ts, local_tz)
        event['details']['timestamp'] = local_dt.strftime('%d %b %Y %H:%M:%S %Z')
        events.append(event)
    return render_template('history.html', hostname=hostname, events=events,
                           page=page, total_pages=pages)


@app.route('/alarms')
def alarms():
    state = request.args.get('state')
    alarms = get_alarms(state)
    alerting = {'alarms': alarms}
    return json.dumps(alerting, default=json_util.default)


@app.route('/status_all')
def status_all():
    alarms = []
    for alarm in mongo.db.alarms.find():
        alarms.append(alarm)
    return json.dumps(alarms, default=json_util.default)


@app.route('/events')
def events():
    skip = request.args.get('skip') if request.args.get('skip') else 0
    limit = request.args.get('limit') if request.args.get('limit') else 10
    events = get_events(skip, limit)
    return json.dumps(events, default=json_util.default)


@app.route('/alarms/<alarm_id>/acknowledge')
def acknowledge(alarm_id):
    oid = ObjectId(alarm_id)
    alarm = mongo.db.alarms.find_one({'_id': oid})
    alarm['acknowledged'] = True
    mongo.db.alarms.save(alarm)
    return redirect(url_for('index'))


@app.route('/alarms/<alarm_id>/clear')
def clear(alarm_id):
    oid = ObjectId(alarm_id)
    alarm = mongo.db.alarms.find_one({'_id': oid})
    alarm['state'] = 'OK'
    alarm['cleared'] = True
    mongo.db.alarms.save(alarm)
    return redirect(url_for('index'))


@app.route('/notification', methods=['POST'])
def notification():
    event = request.get_json()
    mongo.db.notifications.save(event)

    hostname = event['entity']['label']
    check_label = event['check']['label']
    alarm_label = event['alarm']['label']

    event_ts = event['details']['timestamp']
    local_tz = app.config['TIME_ZONE']
    local_dt = utc_timestamp_to_local(event_ts, local_tz)

    alarm_details = {
        'state': event['details']['state'],
        'status': event['details']['status'],
        'timestamp': local_dt.strftime('%d %b %Y %H:%M:%S %Z'),
        'acknowledged': False,
        'cleared': False,
        'state_label': get_state_label(event['details']['state'])
    }

    update_alarm(hostname, check_label, alarm_label, **alarm_details)
    return 'OK'
