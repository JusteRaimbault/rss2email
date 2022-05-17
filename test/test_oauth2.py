#!/usr/bin/env python3

import rss2email.email

message = rss2email.email.get_message(
      sender='rss <rss.raimbaultjwin@gmail.com>',
      recipient='rss <rss.raimbaultjwin@gmail.com>',
      subject='Test',
      body='TEST rss2email - oauth\\n\\n',
      content_type='plain'
  )

rss2email.email.oauth2gmail_send(message)
