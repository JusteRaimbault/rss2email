#!/usr/bin/python
"""rss2email: get RSS feeds emailed to you
http://www.aaronsw.com/2002/rss2email

Usage: python rss2email.py feedfile action [options]
  feedfile: name of the file to store feed info in
  action [options]:
	new [youremail] (create new feedfile)
	email [yournewemail] (update defauly email)
	run
	add feedurl [youremail]
	list
	delete n
"""
__version__ = "2.21"
__author__ = "Aaron Swartz (me@aaronsw.com)"
__copyright__ = "(C) 2004 Aaron Swartz. GNU GPL 2."
___contributors__ = ["Dean Jackson (dino@grorg.org)", 
					 "Brian Lalor (blalor@ithacabands.org)",
					 "Joey Hess", 'Matej Cepl']

### Vaguely Customizable Options ###

# The email address messages are from by default:
DEFAULT_FROM = "bozo@dev.null"

# 1: Receive one email per post
# 0: Receive an email every time a post changes
TRUST_GUID = 1

# 1: Treat the contents of <description> as HTML
# 0: Send the contents of <description> as is, without conversion
TREAT_DESCRIPTION_AS_HTML = 1

# 1: Apply Q-P conversion (required for some MUAs)
# 0: Send message in 8-bits
# http://cr.yp.to/smtp/8bitmime.html
QP_REQUIRED = 0

def send(fr, to, message):
	os.popen2(["/usr/sbin/sendmail", to])[0].write(message)
	
# def send(fr, to, message):
# 	import smtplib
# 	s = smtplib.SMTP("vorpal.notabug.com:26")
# 	s.sendmail(fr, [to], message)

### End of Options ###

# Read options from config file if present.
import sys
sys.path.append(".")
try:
	import config
	DEFAULT_FROM = config.DEFAULT_FROM
	TRUST_GUID = config.TRUST_GUID
	TREAT_DESCRIPTION_AS_HTML = config.TREAT_DESCRIPTION_AS_HTML
except:
	pass

from html2text import html2text, expandEntities
import feedparser
import cPickle as pickle, fcntl, md5, time, os
if QP_REQUIRED: import mimify; from StringIO import StringIO as SIO
def isstr(f): return isinstance(f, type('')) or isinstance(f, type(u''))

def e(obj, val):
	x = expandEntities(obj[val])
	if type(x) is unicode: x = x.encode('utf-8')
	return x.strip()

def getContent(item, url):
	if item.has_key('content') and item['content']:
		for c in item['content']:
			if c['type'] == 'text/plain': return c['value']

		for c in item['content']:
			if c['type'].find('html') != -1:
				return html2text(c['value'], c['base'])
		
		return item['content'][0]['value']
			
	if item.has_key('description'): 
		if TREAT_DESCRIPTION_AS_HTML:
			return html2text(item['description'], url)
		else:
			return item['description']
	
	if item.has_key('summary'): return item['summary']
	return ""

def getID(item, content):
	if TRUST_GUID:
		if item.has_key('id') and item['id']: return item['id']

	if content: return md5.new(content).hexdigest()
	if item.has_key('link'): return item['link']
	if item.has_key('title'): return md5.new(item['title']).hexdigest()

class Feed:
	def __init__(self, url, to):
		self.url, self.etag, self.modified, self.seen = url, None, None, {}
		self.to = to		

def load():
	ff2 = open(feedfile, 'r')
	feeds = pickle.load(ff2)
	fcntl.flock(ff2, fcntl.LOCK_EX)
	return feeds, ff2

def unlock(feeds, ff2):
	pickle.dump(feeds, open(feedfile, 'w'))
	fcntl.flock(ff2, fcntl.LOCK_UN)
	
def add(url, to=None):
	feeds, ff2 = load()
	if not isstr(feeds[0]) and to is None:
		raise 'NoEmail', "Run `email newaddr` or `add url addr`."
	feeds.append(Feed(url, to))
	unlock(feeds, ff2)

def run():
	feeds, ff2 = load()

	if isstr(feeds[0]): default_to = feeds[0]; ifeeds = feeds[1:]
	else: ifeeds = feeds
	
	for f in ifeeds:
		result = feedparser.parse(f.url, f.etag, f.modified)
		
		if result.has_key('encoding'): enc = result['encoding']
		else: enc = 'utf-8'
		
		c, ert = result['channel'], 'errorreportsto'
		
		headers = "From: "
		if c.has_key('title'): headers += e(c, 'title') + ' '
		if c.has_key(ert) and c[ert].startswith('mailto:'):
			fr = c[ert][8:]
		else:
			fr = DEFAULT_FROM
		
		headers += '<'+fr+'>'
				
		headers += "\nTo: " + (f.to or default_to) # set a default email!
		if not QP_REQUIRED:
			headers += '\nContent-Type: text/plain; charset="' + enc + '"'
		
		if not result['items'] and ((not result.has_key('status') or (result.has_key('status') and result['status'] != 304))):
			print "W: no items; invalid feed? (" + f.url + ")"
			continue
	
		for i in result['items']:
			content = getContent(i, f.url)
			id = getID(i, content)
		
			if i.has_key('link'): frameid = link = e(i, 'link')
			else: frameid = id; link = None
			
			if f.seen.has_key(frameid) and f.seen[frameid] == id:
				continue # have seen
	
			if i.has_key('title'): title = e(i, 'title')
			else: title = content[:70].replace("\n", " ")
				
			message = (headers
					   + "\nSubject: " + title
					   + "\nDate: " + time.strftime("%a, %d %b %Y %H:%M:%S -0000", time.gmtime())
					   + "\nUser-Agent: rss2email"
					   + "\n")
			
			message += "\n" + content.strip() + "\n"
			
			if link: message += "\nURL: " + link + "\n"
			
			if QP_REQUIRED:
				mimify.CHARSET = enc
				ins, outs = SIO(message), SIO()
				mimify.mimify(ins, outs); outs.seek(0)
				message = outs.read()
			
			send(fr, (f.to or default_to), message)
	
			f.seen[frameid] = id
			
		f.etag, f.modified = result.get('etag', None), result.get('modified', None)
	
	unlock(feeds, ff2)

def list():
	feeds, ff2 = load()
	
	if isstr(feeds[0]):
		default_to = feeds[0]; ifeeds = feeds[1:]; i=1
		print "default email:", default_to
	else: ifeeds = feeds; i = 0
	for f in ifeeds:
		print `i`+':', f.url, '('+(f.to or ('default: '+default_to))+')'
		i+= 1

	unlock(feeds, ff2)

def delete(n):
	feeds, ff2 = load()
	feeds = feeds[:n] + feeds[n+1:]
	unlock(feeds, ff2)
	
def email(addr):
	feeds, ff2 = load()
	if isstr(feeds[0]): feeds[0] = addr
	else: feeds = [addr] + feeds
	unlock(feeds, ff2)

if __name__ == "__main__":
	if len(sys.argv) < 3: print __doc__
	else: 
		feedfile, action = sys.argv[1], sys.argv[2]
		
		if action == "run": run()
		elif action == "email":
			email(sys.argv[3])
			print "Warning: Feed IDs may have changed. Run `list` before `delete`."
		elif action == "add": add(*sys.argv[3:])
		elif action == "new": 
			if len(sys.argv) == 4: d = [sys.argv[3]]
			else: d = []
			pickle.dump(d, open(feedfile, 'w'))
		elif action == "list": list()
		elif action == "delete": delete(int(sys.argv[3]))
		else:
			print __doc__
		