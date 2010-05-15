#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import re
import datetime
import collections
import random
import os

logging.basicConfig(level=logging.DEBUG)

SEP="-"*77 + "\n"

APP_NAME = "Snippet Manager"
APP_VERSION = "0.1"

DATA_DIRECTORY = "/home/bthomson/.snippets"

snippets = []

categories = set()

def strip_unicode(text):
  # replace this with a compiled regex if its too slow
  text, _ = re.subn(u"\u2018", "`", text)
  text, _ = re.subn(u"\u201B", "`", text)
  text, _ = re.subn(u"\u2035", "`", text)
  text, _ = re.subn(u"\u2032", "'", text)
  text, _ = re.subn(u"\u2019", "'", text)
  text, _ = re.subn(u"\u2015", "--", text)
  text, _ = re.subn(u"\u2014", "--", text)
  text, _ = re.subn(u"\u2013", "-", text)
  text, _ = re.subn(u"\u2012", "-", text)
  text, _ = re.subn(u"\u2011", "-", text)
  text, _ = re.subn(u"\u2010", "-", text)
  text, _ = re.subn(u"\u2026", "...", text)
  text, _ = re.subn(u"\u2033", '"', text)
  text, _ = re.subn(u"\u201C", '"', text)
  text, _ = re.subn(u"\u201D", '"', text)
  text, _ = re.subn(u"\u201F", '"', text)
  text, _ = re.subn(u"\u2036", '"', text)
  return text

class Snippet(object):
  @property
  def rep_rate(self):
    return self._rep_rate

  @rep_rate.setter
  def rep_rate(self, value=None):
    if value < 1:
      value = 1
    elif value > 9:
      value = 9
    self._rep_rate = value


  def __init__(self, read_count, text, category, added, source=None):
    # If this takes up too much ram, you can memory map the files and store
    # offsets instead

    self.text = text

    if source:
      self.source = source

    self.rep_rate = 5
    self.added = added
    self.read_count = read_count
    self.category = category

    categories.add(category)

  def unfscked_text(self):
    # regex replaces single line breaks with spaces and leaves double line breaks
    return re.subn("(?<!\n)\n(?!\n)", " ", self.text)[0]

  def rep_rate_slider_txt(self):
    return {
      1: "Less <X---|----> More",
      2: "Less <-X--|----> More",
      3: "Less <--X-|----> More",
      4: "Less <---X|----> More",
      5: "Less <----X----> More",
      6: "Less <----|X---> More",
      7: "Less <----|-X--> More",
      8: "Less <----|--X-> More",
      9: "Less <----|---X> More",
    }[self.rep_rate]

def import_simple_fmt():
  """for old manual files"""
  with open("/home/bthomson/manual_snippets/pua.txt", 'r') as f:
    data = f.read().decode("UTF-8")

  data = strip_unicode(data)

  SEP2="-"*74 + "\n"

  entries = re.split(SEP2, data)
  for entry_text in entries:
    if entry_text.startswith("http://"):
      url, _, entry_text = entry_text.partition("\n")
    if len(entry_text) > 3:
      snippets.append(Snippet(text=entry_text,
                              category="pua",
                              source=url,
                              added=datetime.datetime.now(),
                              read_count=0))

def write_to_one_file():
  return
  with open("single-file-output.txt", 'w') as f:
    for snippet in snippets.values():
      for param in ['read_count', 'category', 'added']:
        f.write("%s: %s\n" % (param, str(getattr(snippet, param))))
      f.write("*\n")
      f.write(snippet.text)
      f.write(SEP)

def write_to_category_files():
  for category in categories:
    with open("%s/%s.txt" % (DATA_DIRECTORY, category.replace(' ', '_')), 'w') as f:
      for snippet in snippets:
        if snippet.category != category:
          continue
        for param in ['read_count', 'added', 'source']:
          try:
            f.write("%s: %s\n" % (param, str(getattr(snippet, param))))
          except AttributeError:
            pass # just source sometimes, for now
        f.write("*\n")
        f.write(snippet.text.encode("UTF-8"))
        f.write(SEP)
  print "Snippet data saved."

def filename_to_category_name(fn):
  return fn.split('.')[0].replace("_", " ")

def read_category_files():
  import os
  import glob

  for infile in glob.glob(os.path.join(DATA_DIRECTORY, '*')):
    path, filename = os.path.split(infile)
    if not filename.startswith("."):
      with open(infile, 'r') as f:
        data = f.read().decode('UTF-8')
      entries = re.split(SEP, data)
      for entry in entries:
        params, _, text = entry.partition("\n*\n")
        if params:
          p_dict = {}
          for param in params.split("\n"):
            name, _, value = param.partition(": ")
            if name == "":
              pass
            elif name == "added":
              p_dict['added'] = datetime.datetime.strptime(value.strip(),
                                                           "%Y-%m-%d %H:%M:%S.%f")
            elif name == "read_count":
              p_dict['read_count'] = int(value)
            elif name == "source":
              p_dict['source'] = value
            else:
              logging.warning("Unknown property '%s'" % name)

          try:
            snippets.append(Snippet(read_count=p_dict.get('read_count', 0),
                                    text=text,
                                    source=p_dict.get('source', None),
                                    category=filename_to_category_name(filename),
                                    added=p_dict['added']))
          except KeyError:
            print "Required property not found"
            print entry
            sys.exit(1)

def get_next_snippet():
  return random.choice(snippets)

def get_chrome_url():
  path = "/home/bthomson/.config/google-chrome/Default/Local Storage/"
  fn = "chrome-extension_hnicdcgmgpandninpijmdjlcbjdlfjba_0.localstorage"

  import sqlite3
  conn = sqlite3.connect(path+fn)
  c = conn.cursor()
  c.execute("""select * from ItemTable""")

  data = {}

  for row in c:
    data[row[0]] = row[1]

  c.close()
  conn.close()

  return data['url']

#import_simple_fmt()
read_category_files()
active_category = categories.pop()
categories.add(active_category)
#write_to_one_file()
#write_to_category_files()

get_chrome_url()

def nice_datesince(the_date):
  """Formats a datetime in terms of earlier today, yesterday, 3 days ago, etc"""
  today = datetime.datetime.now()
  days_today = (today - datetime.datetime(2008, 1, 1)).days
  days_at_dt = (the_date - datetime.datetime(2008, 1, 1)).days

  delta_seconds = (today - the_date).seconds

  delta_days = days_today - days_at_dt
  if delta_seconds < 60:
    return "Just now"
  if delta_days == 0:
    return "Earlier today"
  elif delta_days == 1:
    return "Yesterday"
  elif delta_days < 7:
    return str(delta_days) + " days ago"
  elif delta_days < 365:
    return "about " + str(delta_days / 7) + " weeks ago"
  else:
    return "about " + str(delta_days / 365) + " years ago"

import urwid

txt_header = ("%s %s - " % (APP_NAME, APP_VERSION) + 
              "Press ? for help")

txt_footer = ("Tracking %d snippets in %d categories." % (len(snippets), len(categories)))
txt_footer_r = ("Active category: %s." % active_category)

# regex replaces single line breaks with spaces and leaves double line breaks
current_snippet = get_next_snippet()

body = urwid.Text("")
source = urwid.Text("")
date_snipped = urwid.Text("")
read_count = urwid.Text("")
category = urwid.Text("")

rep_rate = urwid.Text("")

blank = urwid.Divider()
listbox_content = [
  blank,
  urwid.Padding(body, ('fixed left' ,2),
                          ('fixed right',2), 20),

  blank,
  urwid.Text("**", align='center'),

  urwid.Padding(source, ('fixed left' ,2),
                        ('fixed right',2), 20),

  urwid.Padding(category, ('fixed left' ,2),
                          ('fixed right',2), 20),

  urwid.Padding(date_snipped, ('fixed left' ,2),
                                    ('fixed right',2), 20),

  urwid.Padding(read_count, ('fixed left' ,2),
                                    ('fixed right',2), 20),

  urwid.Padding(rep_rate, ('fixed left' ,2),
                          ('fixed right',2), 20),

]

def update_view(snippet):
  snippet.read_count += 1

  try:
    source.set_text("      Source: %s" % snippet.source)
  except AttributeError:
    source.set_text("      Source: <unknown>")

  date_str = snippet.added.strftime("%A, %B %d %Y @ %I:%M%p")
  delta_str = nice_datesince(snippet.added)
  date_snipped.set_text("Date Snipped: %s (%s)" % (date_str, delta_str))

  category.set_text("    Category: %s" % snippet.category)

  if snippet.read_count == 0:
    rs = "Clipped just now."
  elif snippet.read_count == 1:
    rs = "First time"
  elif snippet.read_count == 2:
    rs = "twice (including this time)"
  else:
    rs = "%d times (including this time)" % snippet.read_count

  body.set_text(snippet.unfscked_text())

  read_count.set_text("        Read: %s" % rs)
  rep_rate.set_text("    Rep rate: %s" % snippet.rep_rate_slider_txt())

update_view(current_snippet)

status = urwid.Text(txt_footer)

listbox = urwid.ListBox(urwid.SimpleListWalker(listbox_content))
header = urwid.AttrMap(urwid.Text(txt_header), 'header')
footer = urwid.AttrMap(
               urwid.Columns([status,
                              urwid.Text(txt_footer_r, align='right')]), 'footer')
frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header, footer=footer)

palette = [
  ('body','black','light gray', 'standout'),
  ('reverse','light gray','black'),
  ('header','white','dark red', 'bold'),
  ('important','dark blue','light gray',('standout','underline')),
  ('editfc','white', 'dark blue', 'bold'),
  ('editbx','light gray', 'dark blue'),
  ('editcp','black','light gray', 'standout'),
  ('bright','dark gray','light gray', ('bold','standout')),
  ('buttn','black','dark cyan'),
  ('buttnf','white','dark blue','bold'),
]


HELP_TEXT = """
  %s is designed to be operated almost exclusively with keyboard.

  o - open source page in web browser
  e - edit current snippet in editor
  """ % APP_NAME

def quit():
  write_to_category_files()
  sys.exit(0)

delete = False

def unhandled(input):
  global current_snippet
  global delete

  sz = screen.get_cols_rows()
  status.set_text(txt_footer)
  if input == "enter":
    import random
    current_snippet = get_next_snippet()
    update_view(current_snippet)

    # scroll to top
    frame.keypress(sz, 'page up')
  elif input == "k":
    frame.keypress(sz, 'up')
  elif input == "j":
    frame.keypress(sz, 'down')
  elif input == "l":
    current_snippet.rep_rate += 1
    rep_rate.set_text("    Rep rate: %s" % current_snippet.rep_rate_slider_txt())
  elif input == "h":
    current_snippet.rep_rate -= 1
    rep_rate.set_text("    Rep rate: %s" % current_snippet.rep_rate_slider_txt())
  elif input == "e":
    import random
    import string
    fn = "st_" + ''.join([random.choice(string.letters) for x in range(20)])
    path = "/tmp/" + fn
    with open(path, 'w') as f:
      f.write(current_snippet.text)

    import pexpect, struct, fcntl, termios, signal, sys
    p = pexpect.spawn('vim %s' % path)

    def sigwinch_passthrough(sig, data):
      """window resize event signal handler"""
      s = struct.pack("HHHH", 0, 0, 0, 0)
      a = struct.unpack('hhhh', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, s))
      p.setwinsize(a[0], a[1])

    handler = signal.getsignal(signal.SIGWINCH)
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    # Small delay required or window won't resize
    import time
    time.sleep(0.100)
    sigwinch_passthrough(None, None)

    try:
      p.interact()
    except OSError:
      # This happens on successful termination sometimes, for some reason
      pass

    # Restore existing handler
    signal.signal(signal.SIGWINCH, handler)

    # Call handler in case window was resized
    handler(None, None)

    with open(path, 'r') as f:
      txt = f.read()

    os.remove(path)

    if txt == current_snippet.text:
      status.set_text("Edit finished. No changes made.")
    else:
      status.set_text("Text updated.")
      current_snippet.text = txt

    update_view(current_snippet)

  elif input == "q":
    quit()
  elif input == "d":
    status.set_text("Really delete? Press y to confirm.")
    delete = True
    return
  elif input == "c":
    pass
  elif input == "s":
    import subprocess
    p = subprocess.Popen(['xclip', '-o'], stdout=subprocess.PIPE)
    data, _ = p.communicate()

    sn = Snippet(text=data,
                 category=active_category,
                 added=datetime.datetime.now(),
                 read_count=-1)
    snippets.append(sn)

    status.set_text("New clip recorded.")
    update_view(sn)
  elif input == " ":
    frame.keypress(sz, 'page down')
  elif input == "?":
    w = urwid.LineBox(urwid.AttrMap(urwid.Text(txt_header), 'header'))

    urwid.Overlay(w, listbox,
                align="center",
                valign="middle",
                width=('relative', 75),
                height=('relative', 75),
                )
  elif input == "y":
    if delete:
      status.set_text("Deleted.")
  elif input == "o":
    try:
      os.system("google-chrome %s" % current_snippet.source)
      status.set_text("Opened URL.")
    except AttributeError:
      url_s = "http://www.google.com/search?&q="
      status.set_text("Source not available; googling phrase.")
      os.system("google-chrome %s" % current_snippet.source)
  delete = False

# Curses module seems to be hosed
screen = urwid.raw_display.Screen()

try:
  loop = urwid.MainLoop(frame, palette, screen, unhandled_input=unhandled).run()
except KeyboardInterrupt:
  quit()
