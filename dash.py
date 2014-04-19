#!/usr/bin/env python

from collections import defaultdict
from flask import jsonify, render_template, request
from heatdash import app
from heatdash import mongo
from heatdash.utils import get_alerts, update_host

app.config['DEBUG'] = True


@app.route('/')
def index():
    alerting = get_alerts()
    return_template('index.html', alerting=alerting)


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


@app.route('/alerts')
def alerts():
    state = request.args.get('state')
    alerting = get_alerts(state)
    return jsonify('alerts'=alerting)


@app.route('/notification', methods=['POST'])
def notification():
    event = request.get_json()
    mongo.db.notifications.save(event)

    hostname = event['entity']['label']
    state = event['details']['state']
    status = event['details']['status']
    update_host(hostname, state, status)
    return 'OK'


if __name__ == '__main__':
    app.run()
