from email.mime.text import MIMEText
from heatdash import app, mongo
from smtplib import SMTP


def email_notification(alarm):
    alarm_text = render_template('alarm_email', alarm=alarm)
    alarm_msg = MIMEText(alarm_text)
    alarm_msg['Subject'] = "** {} {} {} **".format(alarm['hostname'],
                                                   alarm['check'],
                                                   alarm['state'])
    alarm_msg['From'] = app.config['SMTP_SENDER']
    alarm_msg['To'] = app.config['SMTP_RECIPIENT']

    smtp = SMTP(app.config['SMTP_SERVER'], app.config['SMTP_PORT'])
    smtp.login(app.config['SMTP_USERNAME'], app.config['SMTP_PASSWORD'])
    smtp.sendmail(app.config['SMTP_SENDER'], app.config['SMTP_RECIPIENT'],
                  alarm_msg.as_string())
    smtp.quit


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
