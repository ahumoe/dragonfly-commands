# (c) Copyright 2016 by Andreas Hagen Ulltveit-Moe
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>

from dragonfly import (
    Key,
    Text,
    ActionBase,
)

from _text_utils import split_dictation

no_key = Key("")

class FormatAction(ActionBase): 
   
    def __init__(self, formatter, prefix=None, suffix=None):
        super(FormatAction, self).__init__()
        self.formatter = formatter
        self.prefix = no_key if prefix == None else prefix
        self.suffix = no_key if suffix == None else suffix

    def _execute(self, data=None):
        words = split_dictation(data["text1"])
        formatted_words = self.formatter(words) 
        action = self.prefix + Text(formatted_words) + self.suffix
        action.execute()

class CamelAction(FormatAction): 
   
    def __init__(self, prefix=None, suffix=None):
        formatter = lambda words: words[0] + "".join(w.capitalize() for w in words[1:])
        super(CamelAction, self).__init__(formatter, prefix, suffix)

class CapsAction(FormatAction): 
   
    def __init__(self, prefix=None, suffix=None):
        formatter = lambda words: "".join(w.capitalize() for w in words)
        super(CapsAction, self).__init__(formatter, prefix, suffix)

class DashAction(FormatAction): 
   
    def __init__(self, prefix=None, suffix=None):
        formatter = lambda words: "-".join(words)
        super(DashAction, self).__init__(formatter, prefix, suffix)

class UpperScoreAction(FormatAction): 
   
    def __init__(self, prefix=None, suffix=None):
        formatter = lambda words: "_".join([word.upper() for word in words])
        super(UpperScoreAction, self).__init__(formatter, prefix, suffix)


class TextAction(ActionBase): 
   
    def __init__(self, prefix=None, suffix=None):
        super(TextAction, self).__init__()
        self.prefix = no_key if prefix == None else prefix
        self.suffix = no_key if suffix == None else suffix

    def _execute(self, data=None):
        clean_words = split_dictation(data["text1"], False)
        text = " ".join(clean_words)
        action = self.prefix + Text(text) + self.suffix
        action.execute()

class TwoCamelAction(ActionBase): 
   
    def __init__(self, prefix=None, middle=None, suffix=None):
        super(TwoCamelAction, self).__init__()
        self.prefix = no_key if prefix == None else prefix
        self.middle = no_key if middle == None else middle
        self.suffix = no_key if suffix == None else suffix
        
    def _execute(self, data=None):
        words1 = split_dictation(data["text1"])
        words2 = split_dictation(data["text2"])
        camel1 = words1[0] + "".join(w.capitalize() for w in words1[1:])
        camel2 = words2[0] + "".join(w.capitalize() for w in words2[1:])
        action = self.prefix + Text(camel1) + self.middle + Text(camel2) + self.suffix
        action.execute()
