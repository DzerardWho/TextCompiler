from arpeggio import RegExMatch as _
import arpeggio as ar


def space():
    return ar.ZeroOrMore(_(r'\t| '))


def escapedText():
    return _(r'(((?:\\|/)(?:\[|\]))|([^[\]]))+')


def plainText():
    return ar.Optional(escapedText)


def escapedTextUntilNewLine():
    return _(r'(((?:\\|/)(?:\[|\]))|([^[\]\n]))+')


def plainTextUntilNewLine():
    return ar.Optional(escapedTextUntilNewLine)


def string():
    return _(r'[><{}@_!#$%^&*./\\0-9a-zA-Z -]*')


def tagName():
    return _(r'[><{}@_!#$%^&*./\\0-9a-zA-Z-]+')


def singleQuote():
    return "'"


def doubleQuote():
    return '"'


def singleQuotedString():
    return singleQuote, _(r'(((?:\\|/)(?:\'))|([^\']))*'), singleQuote


def doubleQuotedString():
    return doubleQuote, _(r"(((?:\\|/)(?:\"))|([^\"]))*"), doubleQuote


def quotedString():
    return [singleQuotedString, doubleQuotedString]


def beginTag():
    return _(r'(?<!\\|/)\[')


def endTag():
    return _(r'(?<!\\|/)\]')


def separator():
    return space, ',', space


def argString():
    return (
        [quotedString, string],
        ar.Optional(
            space,
            '=',
            space,
            [quotedString, string]
        )
    )


def listOfStrings():
    return '[', ar.ZeroOrMore(argString, sep=separator), ']'


def argument():
    return [argString, listOfStrings]


def args():
    return (beginTag, ar.OneOrMore(argument, sep=separator), space, endTag)


def tag():
    return (space, tagName, space, ar.Optional(args), space)


def tagSelected():
    return (
        beginTag,
        ar.OneOrMore(tag, sep=separator),
        ar.Optional(':', text),
        endTag
    )


def beginOneLineTag():
    return _(r'(?<!\\|/)\[\[')


def oneLineTag():
    return (
        beginOneLineTag,
        ar.OneOrMore(tag, sep=separator),
        ar.Optional(':', textUntilNewLine),
        ['\n', endTag, ar.EOF]
    )


def text():
    return ar.ZeroOrMore([oneLineTag, tagSelected, plainText])


def textUntilNewLine():
    return ar.ZeroOrMore([oneLineTag, tagSelected, plainTextUntilNewLine])


def entrypoint():
    return text, ar.EOF