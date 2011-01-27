#!/usr/bin/env python
# -*- coding: ascii -*-

import collections
import cPickle
import datetime
import logging
import os
import random
import re
import string
import subprocess
import sys
import textwrap
import time
import urllib

import similar
import io

from unidecode import unidecode
from inflect import engine as inflect_engine

inflect = inflect_engine()

logging.basicConfig(level=logging.DEBUG)

APP_NAME = "Snippet Manager"
APP_VERSION = "0.1"

# After pressing return to advance to the next item, you can't advance again
# for this many seconds (prevents accidental key presses)
NEXT_ITEM_DELAY = 3

snippets = []

text_filter = True

# Initially, all categories are up for review
review_category_lock = False

all_flags = set()
categories = set()
needs_reading = set()

sticky_source = None

# TODO: Remove # and ? from the hashed url
source_url_count = collections.defaultdict(int)

next_24_h_count = 0

is_url = re.compile(r"http://").match

def minmax(min_val, val, max_val):
  return max(min_val, min(max_val, val))

def set_term_title(text, show_extra=True):
  if show_extra:
    text = "%s - %s" % (APP_NAME, text)
  print '"\033]0;%s\007"' % text

def rewrap_text(text):
  import textwrap

  paragraphs = []
  for paragraph in text.split("\n\n"):
    paragraphs.append(textwrap.fill(paragraph, 78))
  return "\n\n".join(paragraphs)

def strip_unicode(text):
  return unidecode(text).encode('ascii', 'ignore')

def get_clip_data():
  p = subprocess.Popen(['xclip', '-o'], stdout=subprocess.PIPE)
  data, _ = p.communicate()
  return strip_unicode(data.decode("UTF-8", 'ignore'))

class Snippet(object):
  """Intended to be completely separate from the user-interface!"""

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
    rc = self.read_count
    rr = self.rep_rate

    calc = 2 * (1.7**(min(rc,6)+3) + (5 - rr) * (0.5*rc + 5))

    # At least one day between reps
    calc = max(1, calc)

    if self.rep_rate == 9:
      return 1
    elif self.rep_rate == 8:
      return 7
    elif self.rep_rate == 7:
      return minmax(7, calc, 21)
    elif self.rep_rate == 6:
      return minmax(7, calc, 42)
    else:
      return max(7, calc)

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

def get_chrome_url():
  ext_id = "oeijackdkjiaodhkeclhamncpbonflbh" #violet
  #ext_id = "pifndjjgfmkdohlnddpikoonfdladamo" #eeepc
  path = "/home/bthomson/.config/google-chrome/Default/Local Storage/"
  fn = "chrome-extension_%s_0.localstorage" % ext_id

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
  except sqlite3.OperationalError:
    return "<unknown>" # Chrome not active, plugin not installed, etc

#import_simple_fmt()

reader = io.read_category_files()
for read_ct, text, last_read, flags, source, cat, rep_rate, added in reader:
  sn = Snippet(read_ct, text, cat, added, last_read, flags, rep_rate, source)

  snippets.append(sn)

  if sn.needs_reading():
    needs_reading.add(sn)
  else:
    if sn.next_24_h():
      next_24_h_count += 1

#active_category = 'misc'
active_category = 'pua'
#write_to_one_file()
#write_to_category_files()

def nice_datesince(the_date):
  """Formats a datetime in terms of earlier today, yesterday, 3 days ago, etc"""
  today = datetime.datetime.now()
  days_today = (today - datetime.datetime(2008, 1, 1)).days
  days_at_dt = (the_date - datetime.datetime(2008, 1, 1)).days

  dt = today - the_date
  delta_seconds = dt.seconds + dt.days*86400

  delta_days = days_today - days_at_dt
  if delta_seconds < 60:
    return "Just now"
  if delta_days == 0:
    return "Earlier today"
  elif delta_days == 1:
    return "Yesterday"
  elif delta_days < 7:
    return "%d days ago" % delta_days
  elif delta_days < 365:
    return "about %d weeks ago" % round(delta_days / 7.0)
  else:
    return "about %0.1f years ago" % (delta_days / 365.0)

def update_view(snippet, counts_as_read=False):
  if not snippet:
    for widget in (category, source, date_snipped, read_count, rep_rate):
      widget.set_text("")

    tui.body.set_text("You don't have any snippets that need review!\n\n"
                  "Try adding some new snippets from the web.")
    return

  if counts_as_read:
    snippet.read_count += 1

  try:
    ss = snippet.source
    tui.source.set_text("      Source: %s <%d>" % (ss, source_url_count[ss]))
  except AttributeError:
    tui.source.set_text("      Source: <unknown>")

  date_str = snippet.added.strftime("%A, %B %d %Y @ %I:%M%p")
  delta_str = nice_datesince(snippet.added)
  tui.date_snipped.set_text("Date Snipped: %s (%s)" % (date_str, delta_str))

  tui.category.set_text("    Category: %s" % snippet.category)

  if snippet.read_count == 0:
    rs = "Clipped just now."
  elif snippet.read_count == 1:
    rs = "First time"
  elif snippet.read_count == 2:
    rs = "twice (including this time)"
  else:
    rs = "%d times (including this time)" % snippet.read_count

  tui.body.set_text(snippet.unfscked_text())

  tui.read_count.set_text("        Read: %s" % rs)

  tui.update_rep_rate(snippet)

  set_term_title(" ".join(snippet.text.split(" ", 5)[:-1])+"...")

  tui.defer_update_similarity()

class TUI(object):
  last_next = 0

  def show_info_screen(self):
    if needs_reading:
      second = "Press return to review your first snippet, or add some new ones."
    else:
      second = "Try adding some new snippets from the web."

    ready_ct = len(needs_reading)

    tui.body.set_text(textwrap.dedent("""
      You have %s ready for review.

      (%s will become ready over the next 24 hours.)

      %s""" % (inflect.no("snippet", ready_ct),
               inflect.no("snippet", next_24_h_count),
               second))[1:])


  def update_rep_rate(self, snippet):
    self.rep_rate.set_text(["    Rep rate: %s <Next rep: " %
                           snippet.rep_rate_slider_txt(),
                           ('standout', "%d days" % snippet.get_days_delay()),
                           " from now>"])

  def update_footer(self, update_status=True):
    if update_status:
      self.status.set_text("Tracking %s in %s; %d are ready for review." % (
        inflect.no("snippet", len(snippets)),
        inflect.no("category", len(categories)),
        len(needs_reading),
      ))
      self.active_cat.set_text("Snipping category: %s " % active_category)

    if review_category_lock:
      txt = review_category_lock
    else:
      txt = "[unlocked]"
    self.review_cat.set_text("Review cat lock: %s" % txt)

  def defer_update_similarity(self):
    self.similarity.set_text("  Similarity: <Checking...>")
    self.loop.set_alarm_in(0.01, similar.update_similarity_callback, user_data=self)

  def sz(self):
    return self.screen.get_cols_rows()

  def cmd_next_snippet(self):
    rem_time = self.last_next - time.time() + NEXT_ITEM_DELAY
    if rem_time > 0:
      self.status.set_text("Whoa, slow down!")
      self.loop.set_alarm_in(rem_time, lambda x,y: self.update_footer())
      return

    if self.current_snippet:
      self.current_snippet.update_read_time()

    if not needs_reading:
      self.show_info_screen()
      return

    while needs_reading:
      self.current_snippet = needs_reading.pop()
      if not review_category_lock or self.current_snippet.category == review_category_lock:
        break

    update_view(self.current_snippet, counts_as_read=True)

    # scroll to top
    def fn(a,b):
      for i in range(3):
        self.frame.keypress(self.sz(), 'page up')
    self.loop.set_alarm_in(0.01, fn)

    self.last_next = time.time()

  def cmd_scroll_up(self):
    self.frame.keypress(self.sz(), 'up')

  def cmd_scroll_down(self):
    self.frame.keypress(self.sz(), 'down')

  def cmd_dump(self):
    with open("/home/bthomson/zippy_dump", 'w') as f:
      cPickle.dump(snippets, f)
    self.status.set_text("Dump complete.")

  def cmd_rep_rate_up(self):
    self.current_snippet.rep_rate += 1
    self.update_rep_rate(self.current_snippet)

  def cmd_rep_rate_down(self):
    self.current_snippet.rep_rate -= 1
    self.update_rep_rate(self.current_snippet)

  def cmd_edit_snippet(self):
    start_txt = self.current_snippet.text
    result_txt = open_editor_with_tmp_file_containing(start_txt)

    if result_txt == start_txt:
      self.status.set_text("Edit finished. No changes made.")
    else:
      self.status.set_text("Text updated.")
      self.current_snippet.text = result_txt

    update_view(self.current_snippet, counts_as_read=False)

  def cmd_new_snippet(self):
    result_txt = open_editor_with_tmp_file_containing("")
    if len(result_txt) < 3:
      self.status.set_text("New clip not created.")
    else:
      self.current_snippet = Snippet(read_count=-1,
                                     text=result_txt,
                                     category=active_category,
                                     source="manually written",
                                     added=datetime.datetime.now(),
                                     last_read=None,
                                     flags=None,
                                     rep_rate=None)
      snippets.append(self.current_snippet)

      self.status.set_text("New clip recorded.")
    update_view(self.current_snippet, counts_as_read=True)

  def cmd_quit(self):
    quit()
    sys.exit(0)

  def cmd_pull_source(self):
    self.current_snippet.source = get_chrome_url()
    self.status.set_text("Source modified.")
    update_view(self.current_snippet, counts_as_read=False)

  def cmd_scroll_active_category_up(self):
    global active_category

    l = sorted(list(categories))
    try:
      active_category = l[l.index(active_category) + 1]
    except IndexError:
      active_category = l[0]

    self.update_footer()

  def cmd_scroll_active_category_down(self):
    global active_category

    l = sorted(list(categories))
    l.reverse()
    try:
      active_category = l[l.index(active_category) + 1]
    except IndexError:
      active_category = l[0]

    self.update_footer()

  def cmd_delete_current_snippet(self):
    self.status.set_text("Really delete? Press y to confirm.")

    def d_hook(input):
      if input == "y":
        self.status.set_text("Deleted.")
        snippets.remove(self.current_snippet)
      else:
        self.status.set_text("Not deleted.")

      self.input_hook = None

    self.input_hook = d_hook

  def cmd_open_category_selector(self):
    if not self.current_snippet:
      self.status.set_text("(no active snippet)")
      return
    self.status.set_text("Change item category")

    self.cb.set_category(self.current_snippet.category)

    self.frame.set_body(self.catbox)

    #catbox_content.set_text("(no matches)")
    #catbox_content.set_text()

    # XXX: Buggy
    def c_hook(input):
      self.status.set_text("Category not changed.")
      self.input_hook = None
      self.frame.set_body(self.mainbox)

    self.input_hook = c_hook

  def cmd_clip(self):
    data = get_clip_data()
    data = data.strip(" ")
    if text_filter:
      data = rewrap_text(data)
    try:
      if data[-1] != "\n":
        data += "\n"
    except IndexError:
      self.status.set_text("Error: no clipboard data.")
    else:
      if sticky_source:
        source = sticky_source
      else:
        source = get_chrome_url()
      sn = Snippet(text=data,
                   source=source,
                   category=active_category,
                   added=datetime.datetime.now(),
                   last_read=datetime.datetime.now(),
                   read_count=0)
      snippets.append(sn)

      self.status.set_text("New clip recorded.")
      update_view(sn)
      self.current_snippet = sn
      self.update_footer()

  def cmd_set_sticky_source(self):
    global sticky_source

    self.status.set_text("Source copied from clipboard. Sticky set.")
    sticky_source = get_clip_data()
    sticky_source.replace("\n", " ")
    try:
      self.current_snippet.source = sticky_source
    except AttributeError:
      pass # No current snippet!
    else:
      update_view(self.current_snippet)

  def cmd_lock_review_topic(self):
    global review_category_lock

    review_category_lock = active_category
    self.status.set_text("Review topic locked to %s." % review_category_lock)
    self.update_footer(False)

  def cmd_undo(self):
    self.status.set_text("undo not yet implemented.")

  def cmd_toggle_text_filter(self):
    global text_filter

    text_filter = not text_filter
    if text_filter:
      self.status.set_text("text filter enabled.")
    else:
      self.status.set_text("text filter disabled.")

  def cmd_pgdn(self):
    self.frame.keypress(self.sz(), 'page down')

  def cmd_help(self):
    self.frame.set_body(self.help_screen)

    def new_hook(input):
      self.input_hook = None
      self.frame.set_body(self.mainbox)

    self.input_hook = new_hook

  def cmd_open_in_browser(self):
    try:
      source = self.current_snippet.source
    except AttributeError:
      pass
    else:
      if is_url(source):
        pipe = subprocess.PIPE
        subprocess.Popen(['google-chrome', source], stdout=pipe, stderr=pipe)
        self.status.set_text("Opened URL.")
        return
    self.status.set_text("Source not available; Googling phrase.")
    self.cmd_search_in_google()

  def cmd_search_in_google(self):
    url_s = "http://www.google.com/search?&q="
    words = self.current_snippet.text.split(" ")
    length = random.randint(6, 10)
    offset = random.randint(length+1, len(words))
    phrase = " ".join(words[offset-length:offset])
    subprocess.Popen(['google-chrome', url_s + urllib.quote('"%s"' % phrase)],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  def cmd_mark_manually_written(self):
    try:
      self.current_snippet.source = "manually written"
    except AttributeError:
      self.status.set_text("No snippet to mark!")
    else:
      update_view(self.current_snippet)

  input_map = {
    'D': cmd_dump,
    'd': cmd_delete_current_snippet,
    'e': cmd_edit_snippet,
    'enter': cmd_next_snippet,
    'h': cmd_rep_rate_down,
    'j': cmd_scroll_down,
    'f': cmd_toggle_text_filter,
    'k': cmd_scroll_up,
    'l': cmd_rep_rate_up,
    'n': cmd_new_snippet,
    'm': cmd_mark_manually_written,
    'q': cmd_quit,
    'p': cmd_pull_source,
    'a': cmd_scroll_active_category_up,
    'z': cmd_scroll_active_category_down,
    'c': cmd_open_category_selector,
    's': cmd_clip,
    'S': cmd_set_sticky_source,
    'u': cmd_undo,
    ' ': cmd_pgdn,
    '?': cmd_help,
    'o': cmd_open_in_browser,
    'O': cmd_search_in_google,
  }


tui = TUI()

def quit():
  if tui.current_snippet:
    tui.current_snippet.update_read_time()

  io.write_to_category_files(categories, snippets)
  set_term_title("Terminal", show_extra=False)

def open_editor_with_tmp_file_containing(in_text):
  fn = "st_" + ''.join(random.choice(string.letters) for x in range(20))
  path = "/tmp/" + fn
  with open(path, 'w') as f:
    f.write(in_text.encode('UTF-8'))

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
    out_text = f.read().decode("UTF-8", 'ignore')

  os.remove(path)

  return out_text

def run_urwid_interface():
  import urwid

  txt_header = (
    "%s %s - " % (APP_NAME, APP_VERSION) + "Press ? for help"
  )

  tui.current_snippet = None

  tui.body = urwid.Text("")
  tui.source = urwid.Text("")
  tui.date_snipped = urwid.Text("")
  tui.read_count = urwid.Text("")
  tui.category = urwid.Text("")
  tui.rep_rate = urwid.Text("")
  tui.similarity = urwid.Text("")

  blank = urwid.Divider()
  listbox_content = [
    blank,
    urwid.Padding(tui.body, ('fixed left' ,2),
                        ('fixed right',2), 20),

    blank,
    urwid.Text("**", align='center'),

    urwid.Padding(tui.source, ('fixed left' ,2),
                          ('fixed right',2), 20),

    urwid.Padding(tui.category, ('fixed left' ,2),
                            ('fixed right',2), 20),

    urwid.Padding(tui.date_snipped, ('fixed left' ,2),
                                ('fixed right',2), 20),

    urwid.Padding(tui.read_count, ('fixed left' ,2),
                              ('fixed right',2), 20),

    urwid.Padding(tui.rep_rate, ('fixed left' ,2),
                            ('fixed right',2), 20),

    urwid.Padding(tui.similarity, ('fixed left' ,2),
                              ('fixed right',2), 20),

  ]

  tui.show_info_screen()
  tui.status = urwid.Text("")
  tui.review_cat = urwid.Text("")
  tui.active_cat = urwid.Text("", align='right')

  tui.update_footer()

  tui.mainbox = urwid.ListBox(urwid.SimpleListWalker(listbox_content))

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
              tui.status.set_text("New subcategory '%s' created." % txt)
              io.has_subcategories.add(txt)
            else:
              tui.status.set_text("New root category '%s' created." % txt)
          categories.add(txt)
          tui.current_snippet.category = txt
        elif tui.current_snippet.category == lbl:
          tui.status.set_text("Category not changed.")
        else:
          tui.current_snippet.category = lbl
          tui.status.set_text("Category changed to: %s." % lbl)

        tui.frame.set_body(tui.mainbox)
        update_view(tui.current_snippet, counts_as_read=False)

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

  tui.cb = CatBox()
  tui.cb.edit = urwid.Edit(caption="Category Name: ")

  tui.catbox = urwid.ListBox(urwid.SimpleListWalker([
    tui.cb.edit,
    blank,
    urwid.Text("Type until the category you want is highlighted below, or use the arrow keys to scroll through the list. Press Ctrl-C to go back without changing the category."),
    blank,
    urwid.Padding(tui.cb.pile,
                  ('fixed left' ,2),
                  ('fixed right',2), 20),
    blank,
  ]))

  header = urwid.AttrMap(urwid.Text(txt_header), 'header')

  footer = urwid.AttrMap(
    urwid.Pile([
      tui.status,
      urwid.Columns([tui.review_cat, tui.active_cat]),
    ]), 'footer'
  )

  tui.frame = urwid.Frame(urwid.AttrWrap(tui.mainbox, 'body'), header=header, footer=footer)

  palette = [
    ('reverse','light gray','black'),
    ('header','white','dark red', 'bold', 'white', '#600'),
    ('footer','white','black'),
    ('standout','light green','black'),
    ('similar','light red','black'),
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
    Key('a', 'cycle active category'),
    Key('c', "change current snippet's category with selector tool"),
    Key('d', 'delete current snippet (after confirmation)'),
    Key('D', 'dump snippets to cPickle file'),
    Key('e', 'edit current snippet in editor'),
    Key('h', "decrease current snippet's rep rate"),
    Key('j', 'scroll down'),
    Key('k', 'scroll up'),
    Key('l', "increase current snippet's rep rate"),
    Key('n', 'open editor, add as new snippet when done'),
    Key('o', "open current snippet's source page in web browser"),
    Key('p', "set current snippet's source to active Chrome URL"),
    Key('q', 'quit {0}'.format(APP_NAME)),
    Key('R', 'lock review topic'),
    Key('S', 'copy source from clipboard and make sticky'),
    Key('s', 'create new snippet from X clipboard'),
  ]

  HELP_TEXT = """
  Although some operations can be performed with a mouse, {0} is designed to be
  operated almost exclusively from the keyboard.

  """.format(APP_NAME)

  for key in main_keys:
    HELP_TEXT += "{0} - {1}\n".format(*key)

  HELP_TEXT += """
  Press escape to return."""

  tui.help_screen = urwid.Filler(urwid.Padding(urwid.Text(HELP_TEXT),
                                           ('fixed left' ,2),
                                           ('fixed right',2), 20), 'top')

  tui.input_hook = None

  def unhandled(input):
    if tui.input_hook:
      tui.input_hook(input)
      return

    tui.update_footer()

    def still_unhandled(tui):
      pass

    tui.input_map.get(input, still_unhandled)(tui)

# Curses module seems to be hosed
  tui.screen = urwid.raw_display.Screen()
  tui.screen.set_terminal_properties(256)
  tui.screen.register_palette(palette)

  def main_loop():
    try:
      tui.loop = urwid.MainLoop(tui.frame, screen=tui.screen, unhandled_input=unhandled)
      tui.loop.run()
    except KeyboardInterrupt:
      quit()
      sys.exit(0)
    except:
      quit()
      raise

  tui.screen.run_wrapper(main_loop)
