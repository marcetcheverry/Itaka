# Rewritten version of http://pastebin.ca/151493
 
def timedelta_in_words(td, join=", ".join):
    """Express a datetime.timedelta using a phrase such as "1 hour, 20 minutes".
    Days, hours and minutes can be listed in the result;
    seconds and anything smaller are ignored.
    You can optionally give the function used to join together the items in the list.
    """
 
    pieces = []
    if td.days:
        pieces.append(plural(td.days, 'day'))
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        pieces.append(plural(hours, 'hour'))
    if minutes or len(pieces) == 0:
        pieces.append(plural(minutes, 'minute'))
    return join(pieces)
 
def plural(count, singular):
    # This is the simplest version; a more general version
    # should handle -y -> -ies, child -> children, etc.
 
    return '%d %s%s' % (count, singular, ("", 's')[count != 1])
 
def and_list(pieces):
    """Join strings into a comma-separated list, using "and" when possible.
    >>> and_list(['egg', 'bacon', 'spam'])
    'egg, bacon and spam'
    """
    if len(pieces) == 1:
        return pieces[0]
 
    return ", ".join(pieces[:-1]) + " and " + pieces[-1]
 
# A few simple unit tests
from datetime import timedelta
assert timedelta_in_words(timedelta(0, 0, 0)) == '0 minutes'
assert timedelta_in_words(timedelta(0, 61, 0)) == '1 minute'
assert timedelta_in_words(timedelta(0, 60 * 60, 0)) == '1 hour'
assert (timedelta_in_words(timedelta(0, (50 * 60 + 12) * 60 + 5, 0))
    == '2 days, 2 hours, 12 minutes')
 
assert timedelta_in_words(timedelta(0, 61, 0), and_list) == '1 minute'
assert (timedelta_in_words(timedelta(0, 65 * 60, 0), and_list)
    == '1 hour and 5 minutes')
assert (timedelta_in_words(timedelta(0, (50 * 60 + 12) * 60 + 5, 0), and_list)
    == '2 days, 2 hours and 12 minutes')