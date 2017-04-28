# (c) Copyright 2016 by Andreas Hagen Ulltveit-Moe
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>

from dragonfly import Key

# Had problems with dragonfly not recognizing some characters
# This file is a workaround (for norwegian keyboards)

release =   Key("shift:up, ctrl:up, alt:up")
lbrace =    release + Key("ctrl:down, alt:down, 7") + release # {
rbrace =    release + Key("ctrl:down, alt:down, 0") + release # }    
lbracket =  release + Key("ctrl:down, alt:down, 8") + release # [
rbracket =  release + Key("ctrl:down, alt:down, 9") + release # ]
hashk  =  Key("s-3")

# Windows Alt Codes
# http://reeddesign.co.uk/pdf/WindowsAltCodes.pdf
backslash = release + Key("alt:down, np9, np2") + release # \
tilde = release + Key("alt:down, np1, np2, np6") + release # ~
pipe = release + Key("alt:down, np1, np2, np4") + release # |
caret = release + Key("alt:down, np9, np4") + release # ^
