Note: ZippySnippy has been replaced by a currently-unreleased tool written
in Go. At some point I will get the new source cleaned up and published.

Philosophy
----------

In some sense, ZippySnippy is a mind programming tool. It is designed to
help you get more out of what you read and make it easier to implement new
habits through repetition.

If you read a lot, you probably decide that most of what you have read was
useless, or, at best, never needs to be read again.

However, 1-10% of what you read you may think: "Wow, that's insightful. I
learned something from that." Or, "This is useful. I want to implement this as
a habit."

Instead of just going on to the next thing and having a 90%+ chance of
completely forgetting about what you've learned, you should record this 1-10%
in ZippySnippy.

ZippySnippy accumulates these "snippets" of information and presents them back
to you for review at gradually-increasing intervals of time.

Whether these snippets come from ebooks, the web, or your own brain is up to
you, although ZippySnippy does have features designed to accelerate all 3
of these common use cases.

Remember: long-term learning and behavior change *requires* repetition. There
is no shortcut you can take to avoid this process.

You can either let your environment dictate what you repeatedly encounter, or
you can take control of the process with a tool like ZippySnippy.

Our aim has been to make this process painless enough that you might be
motivated enough to start doing it.

--

The author is surprised by how often he has detected his own behavior change
as a result of ZippySnippy use, *even in areas where he was convinced no
further study was necessary.*

QuickStart
----------

[...]

Source Material
---------------

E-books
*******

After you get used to ZippySnippy you will find printed books annoying. You
can highlight and underline in a printed book, but it is not nearly as
effective as taking the most relevant snippets of text and putting them into
your ZippySnippy rotation.

The Web
*******

You Own Brain
*************

When you have an idea or important thought that you are not going to take
action on immediately, you should take a few seconds to record it in your
ZippySnippy rotation before you forget. You can decide whether it is important
and take action on it later.

Habit
-----

If you are not willing to start using Snippet Manager habitually (like you use
your web browser or email program), it will not be useful to you. You should
stop reading now because you are wasting your time.

On the other hand, if you develop the habit of using it, it can greatly
improve the quality of your recreational reading.

ZippySnippy should be used at least weekly whether you have anything new to
store or not. After some weeks of use, old snippets will come up for review
every day, although it is perfectly okay to let the review queue get big.

Browsing for new knowledge on the web gives more instant gratification than
reviewing existing knowledge. If you use a feed reader, you may find yourself
opening it several times a day, feeling that something important is right
around the corner.

But your lifetime payoff will be better if you strive for mastery over existing
knowledge first.

As the years go by you will be surprised by the quality of the material
ZippySnippy presents. Many items you will have nearly forgotten the content by
the time it comes up for review again, but you will still judge it to be
unusually important and relevant.

.. Many people, if they even _get_ to the point of acquiring useful knowledge in
   their free time (instead of consuming entertainment) make the mistake of
   failing to ever act on 90% of this knowledge. Don't let this be you. Take
   control of your learning process.

Motivation and Credit
---------------------

Snippet Manager was motivated by my love for (but irreconcilable differences
with) SuperMemo, an excellent Windows-based tool for incremental reading and
fact memorization.

I used SuperMemo in a virtual machine for more than a year but the terrible
level of integration with unix tools, proprietary data format, and difficulty
of preventing catastrophic data loss in an automated fashion encouraged me to
develop a new tool that would solve these problems.

I also felt that the Piotr's goal of reducing knowledge down to fact->recall
pairs, while admirable, was inapproprate for probably 90% of my knowledge.
In many of my areas of interest (programming, art, etc) people do not
necessarily even agree on what the facts are. Thus, Snippet Manager is not
designed to assist with the recall of facts through clozes, etc.

Usage and Tips
--------------

Many of the tips for using SuperMemo effectively also apply to ZippySnippy.
For example, a good workflow is to scan quickly over a piece of text, snip it,
and then immediately move on to the next thing.

Any editing should be performed during subsequent review sessions, not during
the first snipping. This is the most efficient way to use your time.
Furthermore, you will often have a better sense of which parts of a text are
worth keeping on the second or third review.

Make entries self-contained
***************************

In general, shorter entries are better than longer ones.

Shorter entries:
  * Can be shuffled more efficiently.
  * Help maintain attention.

Big lists should almost always be broken up into smaller entries. Be careful
when you do this to make sure you retain enough context that you remember what
the entry is talking about the next time you see it.

--

Snippet Manager uses human-readable and human-editable utf8-encoded text files
for all stored data. The format is open and documented. This is terribly
inefficient but important in the event of a bug or partial data loss.

Similarity Matching
-------------------

Once you have collected thousands of snippets and see many of them once a year
or less, it's easy to start forgetting what's in there and accidentally snip
something twice. To help keep your database clean, snippet manager performs
similarity checking and alerts you when one snippet is too similar to another
snippet by highlighting the matching characters.

To keep the similarity match fast, matching snippets are determined through a
sentence-by-sentence comparison. Non-sentence-ending punctuation and case are
ignored, so these two sentences would be considered a match:

  thats interESTING man i never thought OF THAT!
  That's interesting, man; I never thought of that.

However, even *one character* of difference in the words will cause two
sentences not to match:

  That's interesting, man; I never thought of that.
  That's enteresting, man; I never thought of that.

If you perform too much spelling correction to a particular snippet such that
none of the sentences match the original anymore and then you snip that item
again, the similarity comparison may fail to detect a match.

On the other hand, this form of matching is fast and catches the vast majority
of duplicates as long as you are snipping paragraph-based content [#similarity_speed]_.

What Snippet Manager Isn't
--------------------------

Being a console-based tool, Snippet Manager supports only plain text, not HTML
or other types of markup. Some basic concessions for markup are made where
appropriate, but Snippet Manager will never include a full HTML parser or
anything of that nature. This means it is inappropriate for some types of
knowledge.

Plain text effectively covers about 90% of my knowledge representation needs,
so this tradeoff seemed worthwhile to help bound the complexity of the program
(an often under-appreciated concern by folks not experienced with the volume
of data that can be accumulated in these applications over months and years of
use).

This restriction is not likely to change in the future, so if you
require heavy markup or graphics for your knowledge, Snippet Manager is
definitely not the tool for you.

While SuperMemo is a rather monolithic tool, Snippet Manager is meant to appeal
to the unix philosophy of doing just one thing well. That one thing is storing
useful text you would like to review again and helping you keep large volumes
of it neatly organized.

--

Categories are completely optional: Snippet Manager will still manage your
snippets just fine if you leave everything in the default category. On the
other hand, categories provide a powerful way to hierarchiaclly organize
knowledge and the provided tools let you do it quickly.

Some advice: don't go overboard on categories at first. It's actually better to
create a small number of categories that are overly broad and reclassify or
create subcategories later as your number of snippets grows and you gain more
experience with the tool and your own interests.

--

If you're convinced you've gotten all the value there is to get out of a
particular snippet, you can delete it to remove it from your collection
completely or set its rep rate to 0 to keep it in the collection but out of
rotation.

Personally, I rarely delete anything unless it was mistakenly added: I just
adjust rates upward or downward a little bit at each repetition depending on my
perceived utility of the item. You may find a snippet more useful in a few
years so it doesn't hurt too much to keep it around at a low rep-rate.

--

Snippet Manager also randomizes the order of rotation so that new associations
are more likely to form.

--

What does ZippySnippy mean?

It's fast, it manages your snippets, and it has 'py' in the name twice because
it's written in Python :)

Customization
-------------

ZippySnippy is written in Python using the urwid library for console-based
applications.

.. [#similarity_speed] Checking speed is O(n) where n is the number of sentences in
  the new text. The number of entries in the database only matters at
  application startup, not at entry-check time.
