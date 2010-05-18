#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys
import logging
import re
import datetime
import collections
import random
import subprocess
import os

logging.basicConfig(level=logging.DEBUG)

SEP="-"*77 + "\n"

APP_NAME = "Snippet Manager"
APP_VERSION = "0.1"

DATA_DIRECTORY = "/home/bthomson/.snippets"

snippets = []

has_subcategories = set()

categories = set()
all_flags = set()

source_url_count = collections.defaultdict(int)

needs_reading = set()

next_24_h_count = 0

def set_term_title(text, show_extra=True):
  if show_extra:
    text = "%s - %s" % (APP_NAME, text)
  print '"\033]0;%s\007"' % text

def rewrap_text(text):
  import textwrap

  paragraphs = []
  for paragraph in text.split("\n\n"):
    paragraphs.append(textwrap.fill(paragraph, 80))
  return "\n\n".join(paragraphs)


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

  def get_days_delay(self):
    # TODO: rep rate should have more effect
    return 2**(min(self.read_count,6)+2) + (5 - self.rep_rate)

  def get_seconds_delay(self):
    return int(60*60*24*self.get_days_delay())

  def get_delta_seconds(self):
    delta = datetime.datetime.now() - self.last_read
    return delta.seconds + delta.days * 86400

  def needs_reading(self):
    if self.get_delta_seconds() > self.get_seconds_delay():
      return True
    else:
      return False

  def next_24_h(self):
    return self.get_seconds_delay() - self.get_delta_seconds() < 86400

  def update_read_time(self):
    self.last_read = datetime.datetime.now()

  def __init__(self,
               read_count,
               text,
               category,
               added,
               last_read,
               flags=None,
               rep_rate=None,
               source=None):

    # If this takes up too much ram, you can memory map the files and store
    # offsets instead
    self.text = text

    if source:
      self.source = source
      source_url_count[source] += 1

    # Stored as a list, not a set, since we do care about ordering in the saved file.
    if flags:
      self.flags = flags
      all_flags.update(flags)
    else:
      self.flags = []

    if rep_rate:
      self.rep_rate = rep_rate
    else:
      self.rep_rate = 5
    self.added = added
    self.last_read = last_read
    self.read_count = read_count
    self.category = category

    categories.add(category)

  def unfscked_text(self):
    # regex replaces single line breaks with spaces and leaves double line breaks
    # any line that starts with "  " keeps the single line break
    return re.subn("(?<!\n)\n(?!\n|  )", " ", self.text)[0]

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
  with open("fn", 'r') as f:
    data = f.read().decode("UTF-8")

  data = strip_unicode(data)

  SEP2="-"*74 + "\n"

  entries = re.split(SEP2, data)
  for entry_text in entries:
    if entry_text.startswith("http://"):
      url, _, entry_text = entry_text.partition("\n")
    if len(entry_text) > 3:
      snippets.append(Snippet(text=entry_text,
                              category="cat",
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
    with open(category_name_to_relative_path(category), 'w') as f:
      for snippet in snippets:
        if snippet.category != category:
          continue
        f.write("%s: %s\n" % ('read_count', snippet.read_count))
        f.write("%s: %s\n" % ('added', snippet.added))
        f.write("%s: %s\n" % ('last_read', snippet.last_read))
        try:
          f.write("%s: %s\n" % ('source', snippet.source))
        except AttributeError:
          pass # no source
        if snippet.flags:
          f.write("%s: %s\n" % ('flags', ",".join(snippet.flags)))
        if snippet.rep_rate != 5:
          f.write("%s: %s\n" % ('rep_rate', snippet.rep_rate))
        f.write("*\n")
        f.write(snippet.text.encode("UTF-8"))
        f.write(SEP)

def relative_path_to_category_name(path):
  """
  >>> relative_path_to_category_name('bash/fin.txt')
  'bash/fin'

  >>> relative_path_to_category_name('bash/fin/fin.txt')
  'bash/fin'
  """
  # TODO: support paths with dots
  s = path.split('.')[0].replace("_", " ")
  path1, file_name = os.path.split(s)
  path2, dir = os.path.split(path1)
  if file_name == dir:
    # file with same name as enclosing dir gets cat path truncated
    cat_path = os.path.join(path2, dir)
    has_subcategories.add(cat_path)
  else:
    cat_path = os.path.join(path2, dir, file_name)
  return cat_path.replace("/", ".")

def category_name_to_relative_path(cn):
  path = cn.replace(".", "/")
  if cn in has_subcategories:
    path, file_name = os.path.split(path)
    path = path + file_name + '/' + file_name

  return path.replace(' ', '_') + ".txt"


def read_directory(dir):
  import os
  import glob

  for infile in glob.glob(os.path.join(dir, '*')):
    path, filename = os.path.split(infile)
    if filename.startswith("."):
      continue

    if os.path.isdir(infile):
      read_directory(infile)
      continue

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
          elif name == "last_read":
            p_dict['last_read'] = datetime.datetime.strptime(value.strip(),
                                                             "%Y-%m-%d %H:%M:%S.%f")
          elif name == "read_count":
            p_dict['read_count'] = int(value)
          elif name == "source":
            p_dict['source'] = value
          elif name == "flags":
            p_dict['flags'] = value.split(',')
          elif name == "rep_rate":
            p_dict['rep_rate'] = int(value)
          else:
            logging.warning("Unknown property '%s'" % name)

        try:
          sn = Snippet(read_count=p_dict.get('read_count', 0),
                       text=text,
                       last_read=p_dict.get('last_read', None),
                       flags=p_dict.get('flags', None),
                       source=p_dict.get('source', None),
                       category=relative_path_to_category_name(infile),
                       rep_rate=p_dict.get('rep_rate', None),
                       added=p_dict['added'])
          snippets.append(sn)

          if sn.needs_reading():
            needs_reading.add(sn)
          else:
            if sn.next_24_h():
              global next_24_h_count
              next_24_h_count += 1

        except KeyError:
          print "Required property not found"
          print entry
          sys.exit(1)

def read_category_files():
  import os
  os.chdir(DATA_DIRECTORY)

  read_directory('')


def get_chrome_url():
  path = "/home/bthomson/.config/google-chrome/Default/Local Storage/"
  fn = "chrome-extension_hnicdcgmgpandninpijmdjlcbjdlfjba_0.localstorage"

  import sqlite3

  try:
    conn = sqlite3.connect(path+fn)
    c = conn.cursor()
    c.execute("""select * from ItemTable""")

    data = {}

    for row in c:
      data[row[0]] = row[1]

    c.close()
    conn.close()

    return data['url']
  except sqllite3.OperationalError:
    return "<unknown>" # Chrome not active or plugin not installed

#import_simple_fmt()
read_category_files()
active_category = sorted(categories)[0]
#write_to_one_file()
#write_to_category_files()

def nice_datesince(the_date):
  """Formats a datetime in terms of earlier today, yesterday, 3 days ago, etc"""
  today = datetime.datetime.now()
  days_today = (today - datetime.datetime(2008, 1, 1)).days
  days_at_dt = (the_date - datetime.datetime(2008, 1, 1)).days

  dt = (today - the_date)
  delta_seconds = dt.seconds + dt.days*86400

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

current_snippet = None

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

def update_rep_rate():
  nr =  "Next rep: %d days from now" % current_snippet.get_days_delay()
  rep_rate.set_text("    Rep rate: %s <%s>" % (current_snippet.rep_rate_slider_txt(), nr))

def update_footer():
  status.set_text("Tracking %d snippets in %d categories." % (len(snippets),
                                                              len(categories)))
  active_cat.set_text("Active category: %s " % active_category)

def update_view(snippet, counts_as_read=False):
  if not snippet:
    category.set_text("")
    source.set_text("")
    date_snipped.set_text("")
    read_count.set_text("")
    rep_rate.set_text("")
    body.set_text("You don't have any snippets that need review!\n\n"
                  "Try adding some new snippets from the web.")
    return

  if counts_as_read:
    snippet.read_count += 1

  try:
    ss = snippet.source
    source.set_text("      Source: %s <%d>" % (ss, source_url_count[ss]))
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

  update_rep_rate()

  set_term_title(" ".join(snippet.text.split(" ", 5)[:-1])+"...")

if needs_reading:
  second = "Press return to review your first snippet, or add some new ones."
else:
  second = "Try adding some new snippets from the web."

body.set_text("""You have %d snippets ready for review.

(%d snippets will become ready over the next 24 hours.)

%s""" % (len(needs_reading), next_24_h_count, second))

status = urwid.Text("")
active_cat = urwid.Text("", align='right')

update_footer()

mainbox = urwid.ListBox(urwid.SimpleListWalker(listbox_content))

class CatBox(object):
  def __init__(self):
    self.cat_buttons = []
    self.pile = urwid.Pile(
      [urwid.Text("Cats:")] + self.get_catbox_contents(), focus_item=1
    )

  def cat_change(self, rb, new_state):
    if new_state == True:
      lbl = rb.get_label()
      if lbl == "New Root Category":
        txt = self.edit.get_edit_text()
        for category in categories:
          if category.startswith(txt):
            # TODO: not sure this is quite right
            status.set_text("New subcategory '%s' created." % txt)
            has_subcategories.add(txt)
          else:
            status.set_text("New root category '%s' created." % txt)
        categories.add(txt)
        current_snippet.category = txt
      elif current_snippet.category == lbl:
        status.set_text("Category not changed.")
      else:
        current_snippet.category = lbl
        status.set_text("Category changed to: %s." % lbl)

      frame.set_body(mainbox)
      update_view(current_snippet, counts_as_read=False)

  def get_catbox_contents(self):
    for x in sorted(categories):
      r = urwid.RadioButton(self.cat_buttons, x, False)
      urwid.connect_signal(r, 'change', self.cat_change)
    r = urwid.RadioButton(self.cat_buttons, "New Root Category", False)
    urwid.connect_signal(r, 'change', self.cat_change)
    return self.cat_buttons

  def set_category(self, cat):
    for button in self.cat_buttons:
      if button.get_label() == cat:
        button.set_state(True, do_callback=False)

cb = CatBox()
cb.edit = urwid.Edit(caption="Category Name: ")

catbox = urwid.ListBox(urwid.SimpleListWalker([
  cb.edit,
  blank,
  urwid.Text("Type until the category you want is highlighted below, or use the arrow keys to scroll through the list. Press Ctrl-C to go back without changing the category."),
  blank,
  urwid.Padding(cb.pile, ('fixed left' ,2),
                         ('fixed right',2), 20),
  blank,
]))

header = urwid.AttrMap(urwid.Text(txt_header), 'header')
footer = urwid.AttrMap(urwid.Columns([status, active_cat]), 'footer')
frame = urwid.Frame(urwid.AttrWrap(mainbox, 'body'), header=header, footer=footer)

palette = [
  ('reverse','light gray','black'),
  ('header','white','dark red', 'bold', 'white', '#600'),
  ('footer','white','black'),
  ('important','dark blue','light gray',('standout','underline')),
  ('editfc','white', 'dark blue', 'bold'),
  ('editbx','light gray', 'dark blue'),
  ('editcp','black','light gray', 'standout'),
  ('bright','dark gray','light gray', ('bold','standout')),
  ('buttn','black','dark cyan'),
  ('buttnf','white','dark blue','bold'),
]

import collections
Key = collections.namedtuple('Key', 'key help_desc')

main_keys = [
  Key('enter', 'display next rep item (if any)'),
  Key('c', "change current snippet's category with selector tool"),
  Key('o', "open current snippet's source page in web browser"),
  Key('e', 'edit current snippet in editor'),
  Key('k', 'scroll up'),
  Key('j', 'scroll down'),
  Key('h', "decrease current snippet's rep rate"),
  Key('l', "increase current snippet's rep rate"),
  Key('n', 'open editor, add as new snippet when done'),
  Key('p', "set current snippet's source to active Chrome URL"),
  Key('d', 'delete current snippet (after confirmation)'),
  Key('s', 'create new snippet from X clipboard'),
  Key('a', 'cycle active category'),
  Key('q', 'quit {0}'.format(APP_NAME)),
]

HELP_TEXT = """
Although some operations can be performed with a mouse, {0} is designed to be
operated almost exclusively from the keyboard.

""".format(APP_NAME)

for key in main_keys:
  HELP_TEXT += "{0} - {1}\n".format(*key)

HELP_TEXT += """
Press escape to return."""

help_screen = urwid.Filler(urwid.Padding(urwid.Text(HELP_TEXT),
                                         ('fixed left' ,2),
                                         ('fixed right',2), 20), 'top')

def quit():
  if current_snippet:
    current_snippet.update_read_time()

  write_to_category_files()
  set_term_title("Terminal", show_extra=False)
  sys.exit(0)

delete = False

def open_editor_with_tmp_file_containing(in_text):
  import random
  import string
  fn = "st_" + ''.join([random.choice(string.letters) for x in range(20)])
  path = "/tmp/" + fn
  with open(path, 'w') as f:
    f.write(in_text)

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
  time.sleep(0.300)
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
    out_text = f.read()

  os.remove(path)

  return out_text

input_hook = None

def unhandled(input):
  global current_snippet
  global active_category
  global delete
  global input_hook

  if input_hook:
    input_hook(input)
    return

  sz = screen.get_cols_rows()
  update_footer()

  if input == "enter":
    if current_snippet:
      current_snippet.update_read_time()

    if needs_reading:
      current_snippet = needs_reading.pop()
      update_view(current_snippet, counts_as_read=True)

    # scroll to top
    frame.keypress(sz, 'page up')
  elif input == "k":
    frame.keypress(sz, 'up')
  elif input == "j":
    frame.keypress(sz, 'down')
  elif input == "l":
    current_snippet.rep_rate += 1
    update_rep_rate()
  elif input == "h":
    current_snippet.rep_rate -= 1
    update_rep_rate()
  elif input == "e":
    start_txt = current_snippet.text
    result_txt = open_editor_with_tmp_file_containing(start_txt)

    if result_txt == start_txt:
      status.set_text("Edit finished. No changes made.")
    else:
      status.set_text("Text updated.")
      current_snippet.text = result_txt

    update_view(current_snippet, counts_as_read=False)
  elif input == "n":
    result_txt = open_editor_with_tmp_file_containing("")
    if len(result_txt) < 3:
      status.set_text("New clip not created.")
    else:
      current_snippet = Snippet(text=result_txt,
                                source="manually written",
                                category=active_category,
                                added=datetime.datetime.now(),
                                read_count=-1)
      snippets.append(current_snippet)

      status.set_text("New clip recorded.")
    update_view(current_snippet, counts_as_read=True)
  elif input == "q":
    quit()
  elif input == "p":
    current_snippet.source = get_chrome_url()
    status.set_text("Source modified.")
    update_view(current_snippet, counts_as_read=False)
  elif input == "a":
    l = sorted(list(categories))
    try:
      active_category = l[l.index(active_category) + 1]
    except IndexError:
      active_category = l[0]

    update_footer()
  elif input == "d":
    status.set_text("Really delete? Press y to confirm.")
    delete = True
    return
  elif input == "c":
    if not current_snippet:
      status.set_text("(no active snippet)")
      return
    status.set_text("Change item category")

    cb.set_category(current_snippet.category)

    frame.set_body(catbox)

    #catbox_content.set_text("(no matches)")
    #catbox_content.set_text()

    def c_hook(input):
      global input_hook
      status.set_text("Category not changed.")
      input_hook = None
      frame.set_body(mainbox)

    input_hook = c_hook
  elif input == "s":
    p = subprocess.Popen(['xclip', '-o'], stdout=subprocess.PIPE)
    data, _ = p.communicate()
    data = strip_unicode(data.decode("UTF-8"))
    data = rewrap_text(data)
    try:
      if data[-1] != "\n":
        data += "\n"
    except IndexError:
      status.set_text("Error: no clipboard data.")
    else:
      sn = Snippet(text=data,
                   source=get_chrome_url(),
                   category=active_category,
                   added=datetime.datetime.now(),
                   last_read=datetime.datetime.now(),
                   read_count=0)
      snippets.append(sn)

      status.set_text("New clip recorded.")
      update_view(sn)
      current_snippet = sn
      update_footer()
  elif input == "u":
    status.set_text("undo not yet implemented.")
  elif input == " ":
    frame.keypress(sz, 'page down')
  elif input == "?":
    frame.set_body(help_screen)
  elif input == "y":
    if delete:
      status.set_text("Deleted.")
      snippets.remove(current_snippet)
  elif input == "o":
    try:
      os.system("google-chrome %s" % current_snippet.source)
      subprocess.Popen(['google-chrome', current_snippet.source])
      status.set_text("Opened URL.")
    except AttributeError:
      import urllib
      url_s = "http://www.bing.com/search?&q="
      status.set_text("Source not available; googling phrase.")
      phrase = " ".join(current_snippet.text.split(" ")[2:12])
      subprocess.Popen(['google-chrome', url_s + urllib.quote('"%s"' % phrase)],
                       stdout=subprocess.PIPE)
  delete = False

# Curses module seems to be hosed
screen = urwid.raw_display.Screen()
screen.set_terminal_properties(256)
screen.register_palette(palette)

def main_loop():
  try:
    loop = urwid.MainLoop(frame, screen=screen, unhandled_input=unhandled).run()
  except KeyboardInterrupt:
    quit()

screen.run_wrapper(main_loop)
