#!/usr/bin/env python
# (c) Copyright 2015 by James Stout
# (c) Copyright 2016 by Andreas Hagen Ulltveit-Moe
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>

"""Library for extracting words and phrases from text."""

import re

def split_dictation(dictation, strip=True):
    """Preprocess dictation to do a better job of word separation. Returns a list of
    words."""

    clean_dictation = str(dictation)

    if strip:
      # Make lowercase.
      clean_dictation = clean_dictation.lower()
      # Strip apostrophe and "the ".
      clean_dictation = re.sub(r"'|^(a |the )", "", clean_dictation)
      # Convert dashes and " a " into spaces.
      clean_dictation = re.sub(r"-| a | the ", " ", clean_dictation)
      # Surround all other punctuation marks with spaces.
      clean_dictation = re.sub(r"(\W)", r" \1 ", clean_dictation)

    # Convert the input to a list of words and punctuation marks.
    raw_words = [word for word
                 in clean_dictation.split(" ")
                 if len(word) > 0]

    # Merge contiguous letters into a single word, and merge words separated by
    # punctuation marks into a single word. This way we can dictate something
    # like "score test case dot start now" and only have the underscores applied
    # at word boundaries, to produce "test_case.start_now".
    words = []
    previous_letter = False
    previous_punctuation = False
    punctuation_pattern = r"\W"
    for word in raw_words:
        current_punctuation = re.match(punctuation_pattern, word)
        current_letter = len(word) == 1 and not re.match(punctuation_pattern, word)
        if len(words) == 0:
            words.append(word)
        else:
            if current_punctuation or previous_punctuation or (current_letter and previous_letter):
                words.append(words.pop() + word)
            else:
                words.append(word)
        previous_letter = current_letter
        previous_punctuation = current_punctuation
    return words