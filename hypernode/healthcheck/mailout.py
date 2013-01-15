import smtplib
from email.mime.text import MIMEText
from smtplib import SMTPSenderRefused, SMTPRecipientsRefused, SMTPDataError, SMTPException
import re
import socket
import requests
import json


def send_mail(smtphost="localhost", smtpport="25", recipient="recipient@hypernode.com", sender="sender@hypernode.com", subject="testsubject", body="testbody"):

    try:
        smtp = smtplib.SMTP(smtphost, smtpport)
    except socket.error as e:
        raise SMTPException("Could not connect to mailserver at %s:%s: %s" % (smtphost, smtpport, e))

    msg = compose_mail(recipient, sender, subject, body)

    """
    Take code from smtplib.sendmail. We need the send return code.
    """
    # Say hello
    smtp.ehlo_or_helo_if_needed()

    # Set sender
    (code, resp) = smtp.mail(sender)
    if code != 250:
        smtp.rset()
        raise SMTPSenderRefused(code, resp, sender)

    # Set recipient
    (code, resp) = smtp.rcpt(recipient)
    if (code != 250) and (code != 251):
        raise SMTPRecipientsRefused([recipient])

    # Send data over
    (code, resp) = smtp.data(body)
    if code != 250:
        smtp.rset()
        raise SMTPDataError(code, resp)

    # Parse response
    match = re.search("queued as (?P<queueid>[0-9A-F]+)$", resp)

    if not match or not match.group('queueid'):
        raise ValueError("Could not find queue id in response: '%s'" % resp)

    smtp.quit()

    return match.group('queueid')


def check_delivery(messageid, loglines):
    if messageid is None:
        raise ValueError("specify a message id")

    matcher = re.compile("%s: .* queued as [0-9A-F]+\)$" % messageid)

    for line in loglines:
        if matcher.search(line):
            return True

    return False


def compose_mail(recipient, sender, subject, body):
    if recipient is None:
        raise ValueError("recipient cannot be None")

    if sender is None:
        raise ValueError("sender cannot be None")

    if subject is None:
        raise ValueError("subject cannot be None")

    if body is None:
        raise ValueError("body cannot be None")

    msg = MIMEText(body)

    msg["subject"] = subject
    msg["from"] = sender
    msg["to"] = recipient

    return msg


def raise_sos(message=""):
    config = get_deployment_config()
    data = {'message': message}
    resp = requests.post(config["sos_url"], data=data)

    if resp.status_code == 200:
        return True

    return False


# Copied from nodeconfig.common.get_config. No tests, waiting for
# shared code
def get_deployment_config():
    filename = "/etc/hypernode/nodeconfig.json"
    with open(filename, 'r') as fd:
        content = fd.read()
        try:
            return json.loads(content)
        except ValueError:
            return {}
