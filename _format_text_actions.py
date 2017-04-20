# (c) Copyright 2016 by Andreas Hagen Ulltveit-Moe
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>

from dragonfly import (
    Key,
    Text,
    ActionBase,
)

from _text_utils import split_dictation

class FormatAction(ActionBase):
    def __init__(self,
                 formatter,
                 prefix=Key(""),
                 suffix=Key(""),
                 preprocess=True):
        super(FormatAction, self).__init__()
        self.formatter = formatter
        self.prefix = prefix
        self.suffix = suffix
        self.preprocess = preprocess

    def _execute(self, data=None):
        words = split_dictation(data["text"], self.preprocess)
        formatted_words = self.formatter(words)
        action = self.prefix + Text(formatted_words) + self.suffix
        action.execute()

# Format: someWords
class CamelAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key("")):
        formatter = lambda words: words[0] + "".join(w.capitalize() for w in words[1:])
        super(CamelAction, self).__init__(formatter, prefix, suffix)

# Format: SomeWords
class CapsAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key("")):
        formatter = lambda words: "".join(w.capitalize() for w in words)
        super(CapsAction, self).__init__(formatter, prefix, suffix)

# Format: some-words
class DashAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key("")):
        formatter = lambda words: "-".join(words)
        super(DashAction, self).__init__(formatter, prefix, suffix)

# Format: some_words
class ScoreAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key("")):
        formatter = lambda words: "_".join(words)
        super(ScoreAction, self).__init__(formatter, prefix, suffix)

# Format: SOME WORDS
class UpperAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key("")):
        formatter = lambda words: " ".join([word.upper() for word in words])
        super(UpperAction, self).__init__(formatter, prefix, suffix)

# Format: SOME_WORDS
class UpperScoreAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key("")):
        formatter = lambda words: "_".join([word.upper() for word in words])
        super(UpperScoreAction, self).__init__(formatter, prefix, suffix)

# Format: somewords
class WordAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key("")):
        formatter = lambda words: "".join(words)
        super(WordAction, self).__init__(formatter, prefix, suffix)

# Format: some words
class TextAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key(""), preprocess=False):
        formatter = lambda words: " ".join(words)
        super(TextAction, self).__init__(formatter, prefix, suffix, preprocess)

# Format: Some words
class PhraseAction(FormatAction):
    def __init__(self, prefix=Key(""), suffix=Key("")):
        formatter = lambda words: words[0].capitalize() + " " + " ".join(words[1:])
        super(PhraseAction, self).__init__(formatter, prefix, suffix, False)


class TwoCamelAction(ActionBase):
    def __init__(self, prefix=Key(""), middle=Key(""), suffix=Key("")):
        super(TwoCamelAction, self).__init__()
        self.prefix = prefix
        self.middle = middle
        self.suffix = suffix

    def _execute(self, data=None):
        words1 = split_dictation(data["text"])
        words2 = split_dictation(data["text2"])
        camel1 = words1[0] + "".join(w.capitalize() for w in words1[1:])
        camel2 = words2[0] + "".join(w.capitalize() for w in words2[1:])
        action = self.prefix + Text(camel1) + self.middle + Text(camel2) + self.suffix
        action.execute()
