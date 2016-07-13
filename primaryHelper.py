# -*- coding: utf-8 -*-
# @Date    : Nov 22  2012
# @Author  : Ram Prakash
# @Version : 1

# This module can be run to generate the keyboard maps and itrans help
# It can also be imported to get the dumped keyboard maps in string form

import json
import QuillPrimary
import os
import shutil
import codecs
import config
import string
try:
    import nevow.tags as T
    import nevow.flat
    import tidy
except ImportError, e:
    print "Warning: Nevow not found... continuing"

loadedMaps = {}
loadedUniqueWords = {}

def prettyXHTML(uglyXHTML):
    options = dict(input_xml=True,
        output_xhtml=True,
        add_xml_decl=False,
        doctype='omit',
        indent='auto',
        tidy_mark=False)
    return str(tidy.parseString(uglyXHTML, **options))

def genHelp_(lang, q, outfile):
    print "Attempting to generate", outfile, "... ",
    help,examples = q.getSchemeHelp()

    def exLister(context, data):
        for input, output, note in data:
            context.tag [ T.tr [
                T.td (class_ = "input") [input.encode('utf-8')],
                T.td (class_ = "output") [output.encode('utf-8')],
                T.td (class_ = "note") [note.encode('utf-8')]
                ]
            ]
        return context.tag

    def processEx(e):
        if len(e) < 1:
            return

        return "Examples", T.ul [ 
                map(lambda x: T.li [x.encode('utf-8')], e) ]

    def processTR(l):
        if len(l) < 1:
            return

        return T.tr [ 
                map(lambda x: T.td [ 
                    x[0].encode('utf-8'), T.em [ x[1].encode('utf-8') ] 
                    ], l) ]

    def processTable(t):
        if len(t) < 1:
            return

        # If list of lists
        if type(t[0]) == type([]):
            return T.table(cellspacing="3", cellpadding="4") [ map(lambda x: processTR(x), t) ]
        else:
            return T.table(cellspacing="3", cellpadding="4") [ processTR(t) ]

    def helpLister(context, data):
        ret = []
        for label, noteex, eachList in help:
            ret.append(T.h4 [ label.encode('utf-8')] )

            for i in noteex:
                if type(i) == type("") or type(i) is unicode:
                    ret.append(T.p(class_="note") [ i.encode('utf-8') ])
                else:
                    ret.append(processEx(i))

            ret.append(processTable(eachList))

        return ret

    t = T.div (id="help") [ 
            T.p (class_ = "heading") [ "QuillPad allows users to type freely without having to follow any strict typing rules. While QuillPad predicts most words correctly, there may be a few cases where the desired word may not appear in the predicted options. Such words can be composed by entering the words in an ITRANS like scheme." ],
            T.p (style = "font-size: 12px") [ "The following examples demonstrate how to write words using the ITRANS like scheme" ],
            T.table (cellspacing="3", cellpadding="4") [
                T.thead [ T.th ["Input"], T.th ["Output"], T.th ],
                T.tbody(render=exLister, data=examples)
                ],
            T.h3 ["Scheme Tables"],
            T.div(render=helpLister, data=help)
            ]

    ts = open('help_template.html').read()
    f = open(outfile, "w")
    lang = lang[0].upper() + lang[1:]
    f.write(string.Template(ts).substitute(lang = lang, content = prettyXHTML(nevow.flat.flatten(t))))
    f.close()
    print "done"

def genHelp(lang, q, outfile):
    print "Attempting to generate", outfile, "... ",
    help,examples = q.getSchemeHelp()

    s = '<div id="help">\n'
    s += '<p class="heading">QuillPad allows users to type freely without having to follow any strict typing rules. While QuillPad predicts most words correctly, there may be a few cases where the desired word may not appear in the predicted options. Such words can be composed by entering the words in an ITRANS like scheme.</p>\n'
    s += '<p style="font-size: 12px">The following examples demonstrate how to write words using the ITRANS like scheme</p>\n'
    s += '<table class="big" cellspacing="3" cellpadding="4">\n'
    s += '<thead>\n<th>Input</th><th>Output</th><th></th></thead>\n'
    for (input,output,note) in examples:
        outLine = '<td class="input">%s</td> <td class="output">%s</td> <td class="note">%s</td></tr>'%(input,output.encode('utf-8'),note.encode('utf-8'))
        s += '<tr>' + outLine + '</tr>'
    s += "</table>\n"

    def processTR(l):
        if len(l) < 1:
            return

        return "<tr>\n%s</tr>\n" % (reduce(lambda x, y: x + '<td class="special">' + 
                    y[0].encode('utf-8') + " <em>(" +
                    y[1].encode('utf-8') + ")</em></td>", l, ""))

    def processTable(t):
        if len(t) < 1:
            return

        out = '<table class="big" cellspacing="3" cellpadding="4">\n'
        # If list of lists
        if type(t[0]) == type([]):
            for i in t:
                out += processTR(i)
        else:
            out += processTR(t)
        return out + '</table>\n'

    def processEx(e):
        if len(e) < 1:
            return

        return "Examples<ul>\n%s</ul>\n" % (reduce(lambda x, y: x + "<li>" + 
                    y.encode('utf-8') + "</li>", e, ""))

    s += '<h3>Scheme Table</h3>\n'
    for (label,noteex,eachList) in help:
        s += '<h4>%s</h4>\n'%label.encode('utf-8')
        for i in noteex:
            if type(i) == type("") or type(i) is unicode:
                s += '<p class="note">%s</p>' % (i.encode('utf-8'))
            else:
                s += processEx(i)

        s += processTable(eachList)

    s += "</div>\n"
    print "done"

    ts = open('help_template.html').read()
    f = open(outfile, "w")
    lang = lang[0].upper() + lang[1:]
    f.write(string.Template(ts).substitute(lang = lang, content = s))
    f.close()

def processLang(lang, q, outfile):
    print "Attempting to generate", outfile, "... ",
    f = open(outfile, "w")
    f.write(lang + "_interfacemap = " + 
            json.encode(q.virtualInterfaceMap).encode('utf-8') + ";\n")
    f.write(lang + "_keymap = " + 
            json.encode({"map": q.getVirtualKB()}).encode('utf-8') + ";\n")
    f.write(lang + "_pattern = /" + 
            repr(q.dumpAksharaPattern())[2:-1] + "/g ;\n")
    f.write(lang + "_zwnjmap = " + json.encode({
        "zwjSignificant": q.zwjSignificant,
        "zwnjSignificant": q.zwnjSignificant,
        "zwjCode": repr(q.zwjCode)[2:-1],
        "zwnjCode": repr(q.zwnjCode)[2:-1],
        "halanth": repr(q.halanth)[2:-1],
        "nukta": repr(q.nukta)[2:-1]
        }) + ";")
    f.close()

    print "done"

def getLangFile(lang):
    # Check if lang is valid, otherwise return empty string
    if loadedMaps.has_key(lang):
        return loadedMaps[lang]
    else:
        return ""

def isDictWord(lang, word):
    try:
        return loadedUniqueWords[lang].has_key(word)
    except KeyError, e:
        return False

def init():
    """ Load the dump files into memory """
    for i in config.langMap:
        try:
            #f = codecs.open("dump/" + i + "_map.js", "r", "utf-8")
            #loadedMaps[i] = f.read()
            #f.close()

            # Load the unique_lang_words.txt files as well
            loadedUniqueWords[i] = dict([(line.split('\t')[0].decode('utf-8'), 1) for line in open(config.langMap[i][1],'r').readlines()])

        except IOError, e:
            print "Failed to load keyboard map file for %s. Exception %s" % (i, e)
        else:
            print "Loaded keyboard map for", i

    # Load the hindi dictionary
    d = loadedUniqueWords['hindi']
    print "Loading hindi dictionary...",
    for line in open('HindiDictionary.txt').readlines():
        d[line.strip().decode('utf-8')] = 1
    print "Done (%d words)" % (len(d.keys()),)

init()
