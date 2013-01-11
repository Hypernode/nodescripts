import logging
import smtplib
from email.mime.text import MIMEText
from smtplib import SMTPSenderRefused, SMTPRecipientsRefused, SMTPDataError
import re


def send_mail(smtphost="localhost", smtpport="25", recipient="recipient@hypernode.com", sender="sender@hypernode.com", subject="testsubject", body="testbody"):
    smtp = smtplib.SMTP(smtphost, smtpport)
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