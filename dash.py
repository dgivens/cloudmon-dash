#!/usr/bin/env python

import json
import pytz
from bson import json_util
from bson.objectid import ObjectId
from datetime import datetime
from flask import jsonify, redirect, render_template, request, url_for
from heatdash import app
from heatdash import mongo
from heatdash.utils import get_alarms, update_alarm
from pytz import timezone

app.config['DEBUG'] = True
app.config['TIME_ZONE'] = 'CST6CDT'


@app.route('/')
def index():
    alarms = get_alarms()
    return render_template('index.html', alarms=alarms)


@app.route('/history/')
@app.route('/history/<hostname>')
def history(hostname=None):
    if hostname:
        events = []
        for event in mongo.db.notifications.find({'entity.label': hostname}):
            events.append(event)
        return render_template('history.html', events=events)

    hosts = []
    for host in mongo.db.hosts.find():
        hosts.append(host)
    return render_template('hosts.html', hosts=hosts)


@app.route('/alarms')
def alarms():
    state = request.args.get('state')
    alarms = get_alarms(state)
    alerting = {'alarms': alarms}
    return json.dumps(alerting, default=json_util.default)


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

    utc = pytz.utc
    utc_dt = datetime.utcfromtimestamp(
                 event['details']['timestamp'] / 1000).replace(tzinfo=utc)
    local_tz = timezone(app.config['TIME_ZONE'])
    local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))
    alarm_details = {
        'state': event['details']['state'],
        'status': event['details']['status'],
        'timestamp': local_dt.strftime('%d %b %Y %H:%M:%S %Z'),
        'acknowledged': False
    }

    if event['details']['state'] == 'OK':
        alarm_details['state_label'] = 'success'
    elif event['details']['state'] == 'WARNING':
        alarm_details['state_label'] = 'warning'
    else:
        alarm_details['state_label'] = 'danger'

    alarm = update_alarm(hostname, check_label, alarm_label, **alarm_details)
    email_notification(alarm)
    return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
