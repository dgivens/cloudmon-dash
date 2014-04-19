from heatdash import mongo


def get_alerts(state=None):
    alerting = []
    if state:
        search = {'state': state}
    else:
        search = {'state': {'$ne': 'OK'}}

    for host in mongo.db.hosts.find(search):
        alerting.append(host)
    return alerting


def update_host(hostname, state, status):
    host = mongo.db.hosts.find_one({'hostname': hostname})
    if host is None:
        host = {}

    host['host'] = host
    host['state'] = state
    host['status'] = status
    mongo.db.hosts.save(host)
