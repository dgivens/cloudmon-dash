#!/usr/bin/env python

import argparse
import pyrax
from cloudmon_dash.utils import get_state_label, utc_timestamp_to_local
from pymongo import MongoClient


def main():
    parser = argparse.ArgumentParser(description='Back-fill check information')
    parser.add_argument('-c', '--creds', default='~/.raxrc', help='Rackspace '
                        'credentials file')
    parser.add_argument('-u', '--username', help='Rackspace Username')
    parser.add_argument('-a', '--apikey', help='Rackspace API Key')
    parser.add_argument('-t', '--timezone', default='CST6CDT', help='Timezone')
    args = parser.parse_args()

    username = args.username
    api_key = args.apikey
    creds_file = args.creds
    timezone = args.timezone

    client = MongoClient()
    db = client.cloudmon_dash

    pyrax.set_setting("identity_type", "rackspace")

    if username and api_key:
        pyrax.set_credentials(username, api_key)
    else:
        pyrax.set_credential_file(creds_file)

    cm = pyrax.cloud_monitoring
    view = cm.get_overview()

    alerts = []
    for item in view['values']:
        for alarm_state in item['latest_alarm_states']:
            alarm = {}
            alarm['hostname'] = item['entity']['label']
            alarm['alarm'] = (alarm['label'] for alarm in item['alarms']
                              if alarm['id'] == alarm_state['alarm_id']).next()
            alarm['check'] = (check['label'] for check in item['checks']
                              if check['id'] == alarm_state['check_id']).next()
            alarm['state'] = alarm_state['state']
            alarm['status'] = ''
            alarm['state_label'] = get_state_label(alarm_state['state'])
            alarm['acknowledged'] = False
            alarm['cleared'] = False
            alarm_ts = alarm_state['timestamp']
            local_dt = utc_timestamp_to_local(alarm_ts, timezone)
            alarm['timestamp'] = local_dt.strftime('%d %b %Y %H:%M:%S %Z')

            db.alarms.save(alarm)

if __name__ == '__main__':
    main()
