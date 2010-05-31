Note: ZippySnippy is currently alpha-quality software. I use it to manage
thousands of snippets, but there are still a lot of rough edges.

ZippySnippy is a console-based tool designed to gradually accumulate
"snippets" of information that you find interesting or useful. ZippySnippy
will then present these snippets back to you for review at gradually increasing
intervals of time.

Whether these snippets come from ebooks, the web, or your own brain is up to
you, although ZippySnippy does have features designed to accelerate all 3
of these common use cases.

Why bother with Snippet Manager? Well, my life has been filled with examples of
learning or reading something useful and then subsequently and quite quickly
forgetting all about it. Long-term learning _requires_ repetition, ideally spaced
at gradually increasing intervals of time. Snippet Manager aims to make this
process painless enough that you might be motivated to start doing it.

QuickStart

[...]

Habit

Snippet Manager should be used at least weekly whether you have anything new to
store or not. After some weeks of use, old snippets will come up for review
every day.

Browsing for new knowledge on the web may give more instant gratification than
reviewing existing knowledge and trying to put it into practice, but your
lifetime payoff will be better if you strive for mastery over existing
knowledge first.

Many people, if they even _get_ to the point of acquiring useful knowledge in
their free time (instead of consuming entertainment) make the mistake of
failing to ever act on 90% of this knowledge. Don't let this be you. Take
control of your learning process.

Motivation and Credit

Snippet Manager was motivated by my love for (but irreconcilable differences
with) SuperMemo, an excellent Windows-based tool for incremental reading and
fact memorization.

I used SuperMemo in a virtual machine for more than a year but the terrible
level of integration with unix tools, proprietary data format, and difficulty
of preventing catastrophic data loss in an automated fashion encouraged me to
develop a new tool that would solve these problems.

I also felt that the Piotr's goal of reducing knowledge down to fact->recall
pairs, while admirable, was inapproprate for probably 90% of my knowledge.
Snippet Manager is not designed to assist with the recall of facts.

Snippet Manager uses human-readable and human-editable utf8-encoded text files
for all stored data. The format is open and documented. This is terribly
inefficient but important in the event of a bug or partial data loss.

What Snippet Manager Isn't

Being a console-based tool, Snippet Manager supports only plain text, not HTML
or other types of markup. Some basic concessions for markup are made where
appropriate, but Snippet Manager will never include a full HTML parser or
anything of that nature. This means it is inappropriate for some types of
knowledge. However, plain text effectively covers about 90% of my knowledge
representation needs, so this tradeoff seemed worthwhile to help bound the
complexity of the program (an often under-appreciated concern by folks not
experienced with the volume of data that can be accumulated in these
applications over months and years of use).  This restriction is not likely to
change in the future, so if you require heavy markup or graphics for your
knowledge, Snippet Manager is definitely not the tool for you.

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
