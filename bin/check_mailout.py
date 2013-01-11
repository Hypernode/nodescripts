#!/usr/bin/env python

import logging
import healthcheck.mailout as mailout

recipient = "testrecipient@hypernode.com"
smtphost = "localhost"
smtpport = "25"

"""

Send a testmail to a testrecipient
    Connect to the local mailserver
    Send the testmail
    Store the message ID

Wait an appropriate time

See if the mail is delivered
    Open the mail logfile
    Check if our message ID shows up
    If the message is sent, we are done
    If the message is not sent, we croak
        Call the SOS server to tell it delivery failed
        Give the error in the callback
"""

logger = logging.getLogger("healthcheck.mailout")


messageid = mailout.send_mail(recipient, smtphost, smtpport)
mailout.wait()
mailout.check_delivery(messageid)

