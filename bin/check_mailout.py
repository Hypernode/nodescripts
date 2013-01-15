#!/usr/bin/env python

import sys
import os
import hypernode.healthcheck.log
import hypernode.healthcheck.mailout as mailout
import time
from hypernode.healthcheck.mailout import SMTPException

recipient = "testrecipient@hypernode.com"
sender = "testsender@hypernode.com"
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

logger = hypernode.healthcheck.log.getLogger("hypernode.healthcheck.mailout")

with open("/var/log/mail.log") as maillog:
    # First, seek to the end of the file, so we get only new entries.
    # This to make sure that we do not process a mail log of 10GB :)
    maillog.seek(0, 2)  # seek to the end, 2 means 0 bytes relative to end

    try:
        logger.debug("Will try to send email from %s to %s through mailserver %s:%s" % (sender, recipient, smtphost, smtpport))
        messageid = mailout.send_mail(smtphost=smtphost, smtpport=smtpport, recipient=recipient, sender=sender)
    except SMTPException as e:
        logger.critical("Could not send test email to %s through %s:%s" % (recipient, smtphost, smtpport))
        logger.critical(e)
        sys.exit(1)

    logger.debug("Giving postfix a few seconds to process the mail")
    time.sleep(10)

    logger.debug("Looking for queue id in delivery log")

    if mailout.check_delivery(messageid, maillog):
        logger.debug("Mail was successfully sent!")
    else:
        # Has the logfile since been rotated?
        # Check inodes to find out
        logger.debug("Checking to see if mail log has been rotated")
        ourstat = os.fstat(maillog.fileno())
        newstat = os.stat("/var/log/mail.log")

        if newstat.st_ino != ourstat.st_ino:
            logger.debug("The logfile has been rotated %d vs %d." % (ourstat.st_ino, newstat.st_ino))
            logger.debug("Skip current check.")
            sys.exit(0)
        else:
            logger.critical("Mail was not sent!")
            # TODO: callback
            sys.exit(1)