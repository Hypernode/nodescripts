import smtplib
from email.mime.text import MIMEText
from smtplib import SMTPSenderRefused, SMTPRecipientsRefused, SMTPDataError, SMTPConnectError, SMTPException
import re
import socket
import requests
import hypernode.nodeconfig.common


def send_mail(smtphost="localhost", smtpport="25", recipient="recipient@hypernode.com", sender="sender@hypernode.com", subject="testsubject", body="testbody"):

    try:
        smtp = smtplib.SMTP(smtphost, smtpport)
    except socket.error as e:
        raise SMTPConnectError(smtphost, smtpport)

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


def raise_sos(message=""):
    config = hypernode.nodeconfig.common.get_config("/etc/hypernode/nodeconfig.json")
    data = {'message': message}
    resp = requests.post(config["sos_url"], data=data)

    if resp.status_code == 200:
        return True

    return False