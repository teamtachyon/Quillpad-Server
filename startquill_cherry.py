# -*- coding: utf-8 -*-
# @Date    : Nov 22  2012
# @Author  : Tachyon Technologies Pvt Ltd
# @Version : 1

from email.MIMEText import MIMEText
from aifc import Error
import cherrypy
from QuillSourceProcessor import QuillSourceProcessor
from QuillManual import QuillManual 
import const
import MySQLdb
import logging
import logging.config
import smtplib
from email.MIMEText import MIMEText
from email.MIMEMessage import MIMEMessage
from email.Header import Header
import email.Utils
import MimeWriter, mimetools, cStringIO
import htmllib, formatter
import time
import re, os, signal, sys
import quilljson as json
import demjson
import QuillPrimary
import config
import urllib2
from cherrypy.process.plugins import PIDFile

logging.config.fileConfig('logsystem.conf')
logger = logging.getLogger('quillpad')

class QuillCherry:
    @cherrypy.expose
    def getCorrections(self, lang, currWord, userInput, pos, rand=None, callback=None, scid=None):
        currWord = currWord.split(",")
        c = self.quillProcessor.getCorrections(lang, 
                [x.decode('utf-8') for x in currWord], userInput, int(pos))
        o = {}
        words = []
        for i in c:
            word = "".join(i)
            o[word] = i
            words.append(word)
        ret = json.encode({'options': words, 'optmap': o})

        if callback:
            ret = "%s(%s,%s)" % (callback, ret, scid)
        return ret

    @cherrypy.expose
    def getCorrectionsStr(self, lang, currWord, userInput, pos, rand=None, callback=None, scid=None):
        c = self.quillProcessor.getCorrectionsStr(lang, currWord.decode('utf-8'), userInput, int(pos))
        o = {}
        words = []
        for i in c:
            word = "".join(i)
            o[word] = i
            words.append(word)
        ret = json.encode({'options': words, 'optmap': o})

        if callback:
            ret = "%s(%s,%s)" % (callback, ret, scid)
        return ret
        
    @cherrypy.expose
    def processText(self, inString,rand,lang):
        self.quillProcessor.switchLanguage(lang)
        return inString + "\n" +   const.optionSeperator.join(self.quillProcessor.processText(inString.lower(), True).split(const.optionSeperator)[:4])

    @cherrypy.expose
    def processWord(self, inString,lang,rand=None):
        self.quillProcessor.switchLanguage(lang)
        if self.preprocs.has_key(lang) :
            if self.preprocs[lang].has_key(inString.lower()) :
                return inString + "\n" + const.optionSeperator.join(self.preprocs[lang][inString.lower()][:4])

        return inString + "\n" +   const.optionSeperator.join(
                self.quillProcessor.processText(inString.lower()).split(const.optionSeperator)[:4])

    @cherrypy.expose
    def xlit(self, inString, lang, rand=None):
        d = self.quillProcessor.xlit(inString, lang)
        return json.encode(d)

    @cherrypy.expose
    def processString(self, inString, lang, rand=None):
        return self.quillProcessor.processString(inString, lang)

    @cherrypy.expose
    def processWordJSON(self, inString, lang, rand=None, callback=None, scid=None):
        d = self.quillProcessor.processWord(inString, lang)
	
        try:
            d['itrans'] = self.quillPrimary[lang].primaryToUnicode(inString)
        except KeyError, e:
            d['itrans'] = inString

        # Adding the preproc words
        if self.preprocs.has_key(lang) :
            if self.preprocs[lang].has_key(inString.lower()):
                preProcWord = self.preprocs[lang][inString.lower()][0]
                if preProcWord in d['twords'][0]['options']:
                    d['twords'][0]['options'].remove(preProcWord)
                d['twords'][0]['options'].insert(0, preProcWord)

        ret = json.encode(d)

        if callback:
            ret = "%s(%s,%s)" % (callback, ret, scid)
        return ret

    @cherrypy.expose
    def processEngWord(self, inString, lang, rand=None, callback=None, scid=None):
        d = self.quillProcessor.processWord(inString, lang)
        
        try:
            d['itrans'] = self.quillPrimary[lang].primaryToUnicode(inString)
        except KeyError, e:
            d['itrans'] = inString

        # Adding the preproc words
        if self.preprocs.has_key(lang) :
            if self.preprocs[lang].has_key(inString.lower()):
                preProcWord = self.preprocs[lang][inString.lower()][0]
                if preProcWord in d['twords'][0]['options']:
                    d['twords'][0]['options'].remove(preProcWord)
                d['twords'][0]['options'].insert(0, preProcWord)

        ret = json.encode({'engOutput': d['twords'][0]['options'][0]})

        if callback:
            ret = "%s(%s,%s)" % (callback, ret, scid)
        return ret
        
    @cherrypy.expose        
    def processAPIWord(self, inString, lang, rand=None, callback=None, scid=None, key=None):
        if key:
            if self.validAPIKeys.has_key(key) and lang in self.validAPIKeys.get(key):
                return self.processWordJSON(inString, lang, rand, callback, scid)
        cherrypy.response.status = 403

    @cherrypy.expose
    def AddAPIKey(self, key=None, lang=None):
        if key and lang:
            lang = lang.lower() 
            if key not in self.validAPIKeys:
                self.validAPIKeys[key] = [lang]                                                        
            elif lang not in self.validAPIKeys[key]:
                self.validAPIKeys[key].append(lang)
            return json.encode({'status': 'Success'})
        return json.encode({'status': 'Error'})
   
    @cherrypy.expose
    def RemoveAPIKey(self, key=None):
        if key: 
            if key in self.validAPIKeys:
                del self.validAPIKeys[key]                                                        
                return json.encode({'status': 'Success'})
        return json.encode({'status': 'Error'})

    @cherrypy.expose
    def GetAPILang(self, key=None, callback=None, id=None):
        s='Error'               
        if key: 
            if key in self.validAPIKeys:
               langs = self.validAPIKeys[key] 
               s = ','.join(langs);                                              
        if callback:
            s = "%s('%s',%s)" % (callback, s, id)
        return s 

    @cherrypy.expose
    def RemoveLanguage(self, key=None, lang=None):
        if key and lang:
            if key in self.validAPIKeys and lang in self.validAPIKeys.get(key):
                self.validAPIKeys.get(key).remove(lang)                                                        
                if len(self.validAPIKeys.get(key)) == 0:
                    del self.validAPIKeys[key]                                                        
                return json.encode({'status': 'Success'})
        return json.encode({'status': 'Error'})

    @cherrypy.expose
    def reverseProcessWord(self, lang, uWord, rand=None, callback=None, scid=None):
        #Added for Accenture
        d = {}
        try:
            d['options'] = self.quillProcessor.processReverseWord(uWord.decode('utf-8'), lang)
        except KeyError, e:
            d['options'] = [] 
            print "Exception: ", e
        
        ret = json.encode(d)
        if callback:
            ret = "%s(%s, %s)" % (callback, ret, scid)
        return ret

    @cherrypy.expose
    def reverseProcessWordJSON(self, lang, uStr1, uStr2, rand=None, callback=None, scid=None):
        d = {}
        try:
            d['engStr1'] = self.quillManual[lang].unicodeToPrimary(uStr1.decode('utf-8'))
            d['engStr2'] = self.quillManual[lang].unicodeToPrimary(uStr2.decode('utf-8'))
        except KeyError, e:
            d['engStr1'] = uStr1
            d['engStr2'] = uStr2
            print "Exception: ", e

        ret = json.encode(d)
        if callback:
            ret = "%s(%s, %s)" % (callback, ret, scid)
        return ret


    @cherrypy.expose
    def primaryToUnicodeCherry(self, literal ,rand, lang) :
        try:
            return literal + "\n" +  self.quillManual[lang].primaryToUnicode( literal )[0]
        except Exception, e:
            logger.error(str(e))
            print e
            return "-------------";

    @cherrypy.expose
    def unicodeToPrimaryCherry(self, uStr ,rand, lang) :
        try:
            return uStr.decode('utf-8') + "\n" + self.quillManual[lang].unicodeToPrimary( uStr.decode('utf-8') )
        except Exception, e:
            logger.error(str(e))
            print e
            return "-------------";    
        
    @cherrypy.expose
    def unicodeToHelperPairCherry(self, uStr, rand, lang):
        try:
            tuplePair = self.quillManual[lang].unicodeToHelperPair( uStr.decode('utf-8') )
            return tuplePair[1] + "\n" + tuplePair[0]
        except Exception, e:
            logger.error(str(e))
            print e
            return "-------------";    
    
    @cherrypy.expose
    def unicodeToHelperStrCherry(self, uStr,rand, lang ) :
        try:
            return uStr.decode('utf-8') + "\n" + self.quillManual[lang].unicodeToHelperStr( uStr.decode('utf-8') )
        except Exception, e:
            logger.error(str(e))
            print e
            return "-------------";
    
    @cherrypy.expose
    def getOptionsAtCherry(self, currHelper, currUStr, pos,rand, lang ) :
        try:
            return currUStr.decode('utf-8') + "\n" + "\n".join(tupleToStrList(self.quillManual[lang].getOptionsAt( currHelper, currUStr.decode('utf-8'), int(pos) )))
        except Exception, e:
            logger.error(str(e))
            print e
            return "-------------";    
    
    @cherrypy.expose
    def getInsertCorrectionsCherry(self, currHelper, currUStr, pos, delta,rand, lang ) :
        try:
            corrections = currUStr.decode('utf-8') + "\n" + "\n".join(tupleToStrList(self.quillManual[lang].getInsertCorrections( currHelper, currUStr.decode('utf-8'), int(pos), delta )));
            return corrections
        except Exception, e:
            logger.error(str(e))
            print e
            return "-------------";
    
    @cherrypy.expose
    def getDeleteCorrectionsCherry(self, currHelper, currUStr, pos, delLen,rand, lang ) :
        try:
            return currUStr.decode('utf-8') + "\n" + "\n".join(tupleToStrList(self.quillManual[lang].getDeleteCorrections( currHelper, currUStr.decode('utf-8'), int(pos), int(delLen) )))
        except Exception, e:
            logger.error(str(e))
            print e
            return "-------------";
        
    @cherrypy.expose
    def getDeleteAndInsertCorrectionsCherry(self, currHelper, currUStr, pos, delLen,rand, lang, insertDelta ) :
        try:
            pos = int(pos)
            delLen = int(delLen)
            deleteCorrectionsTuple = tupleToStrList(self.quillManual[lang].getDeleteCorrections( currHelper, currUStr.decode('utf-8'), pos, delLen ))
            newHelper = currHelper[0:pos] + currHelper[pos+delLen:]
            print "newHelper : " + newHelper
            newCurrUStr = deleteCorrectionsTuple[0];
            return currUStr.decode('utf-8') + "\n" + "\n".join(tupleToStrList(self.quillManual[lang].getInsertCorrections( newHelper, newCurrUStr, int(pos), insertDelta )));
            
        except Exception, e:
            logger.error(str(e))
            print e
            return "-------------";

    def loadPreprocs(self,preprocsListFile) :
        self.preprocs = {}
        lines = open(preprocsListFile).readlines()
        for line in lines[1:] :
            (lang,file) = line.split()
            self.preprocs[lang] = {}
            preprocLines = open(file,'rb').readlines()
            for preprocLine in preprocLines[1:] :
                l = preprocLine.strip().decode('utf-8').split()
                self.preprocs[lang][l[0].lower()] = l[1:]

    def buildPrimary(self):
        self.quillPrimary = {}
        for lang in config.langMap:
            print "Loading primary rules for", lang, "...",
            self.quillPrimary[lang] = QuillPrimary.QuillRuleBased(config.langMap[lang][0])
            print "done"

    def __init__(self):
        self.processWordDict = {}
        self.validAPIKeys = {}
        self.quillProcessor = QuillSourceProcessor()
        self.quillManual= {"hindi": QuillManual("Hindi_Primary.xml"),"kannada": QuillManual("Kannada_Primary.xml"), "malayalam": QuillManual("Malayalam_Primary.xml"), "marathi": QuillManual("Marathi_Primary.xml"), "tamil": QuillManual("Tamil_Primary.xml"),"telugu": QuillManual("Telugu_Primary.xml")}
        self.loadPreprocs("preProcessedWordFiles.txt")
        self.buildPrimary()
    
    @cherrypy.expose
    def saveErrorMessage(self, message, version, sessionid, rand, lang):
        insert_dict = {'message':message, 'version':version, 'sessionid':sessionid, 'language':lang}
        sql = insertFromDict("error_log", insert_dict)
        
        try:
            cursor = cherrypy.thread_data.db.cursor()
        except Exception, e:
            connect()
            cursor = cherrypy.thread_data.db.cursor()
            logger.warn(str(e))
            
        cursor.execute(sql, insert_dict)
        cursor.close()
        
    @cherrypy.expose
    def saveFeedback(self, message, name, email, version, sessionid, rand, lang):
        insert_dict = {'message':message,'name':name,'email':email, 'version':version, 'sessionid':sessionid, 'language':lang, "remote_addr": cherrypy.request.headers['x-forwarded-for'][-90:]}
        sql = insertFromDict("feedback", insert_dict)
        try:
            cursor = cherrypy.thread_data.db.cursor()
        except Exception, e:
            connect()
            cursor = cherrypy.thread_data.db.cursor()
            logger.warn(str(e))
        
        cursor.execute(sql, insert_dict)
        cursor.close()

    def sendMail(self, email_to, email_from, email_replyto, email_subject, html_message, lang):
        try:
            #msg = ("From: %s\r\nTo: %s\r\nReply-To: %s\r\n\r\n" % (email_from + "<quill@tachyon.in>", ", ".join(email_to.split()), email_replyto))

            server = smtplib.SMTP(const.SMTP_SERVER_URL)
            if len(const.SMTP_LOGIN_USER) != 0:
                server.login( const.SMTP_LOGIN_USER, const.SMTP_LOGIN_PASSWD) 
            #server.set_debuglevel(1)
            send_emails_to = email_to.split(',');
            send_emails_to.append(email_replyto);
            server.sendmail(email_from + "<quill@tachyon.in>", send_emails_to, html_message)
            server.quit()
            
            #recording this in the db
            insert_dict = {'lang':lang, 'mail_count':len(email_to.split(','))}
            sql = insertFromDict("emails_sent", insert_dict)
            try:
                cursor = cherrypy.thread_data.db.cursor()
            except Exception, e:
                connect()
                cursor = cherrypy.thread_data.db.cursor()
                logger.warn(str(e))
                
            cursor.execute(sql, insert_dict)
            cursor.close()
            return "success"
        except Exception, e:
            print e
            logger.error(str(e))
            return "failed"

    @cherrypy.expose
    def sendHTMLEmail(self, email_to, email_from, email_replyto, email_subject, email_message, email_message_html, rand, lang):
        html_message = createhtmlmail(email_subject, email_message, 
            getFormattedHTML(email_message_html, lang), email_from + " <quill@tachyon.in>", email_to, email_replyto)
        self.sendMail(email_to, email_from, email_replyto, email_subject, html_message, lang)
    
    @cherrypy.expose
    def sendEmail(self, email_to, email_from, email_replyto, email_subject, email_message, version, sessionid, rand, lang):
        html = getHTML(email_message, lang)
        textout = cStringIO.StringIO( )
        formtext = formatter.AbstractFormatter(formatter.DumbWriter(textout))
        parser = htmllib.HTMLParser(formtext)
        parser.feed(html)
        parser.close( )
        text = textout.getvalue( )
        html_message = createhtmlmail(email_subject, text, html, email_from + " <quill@tachyon.in>", email_to, email_replyto)
        self.sendMail(email_to, email_from, email_replyto, email_subject, html_message, lang)
    
    @cherrypy.expose
    def saveNewWordMapping(self, rand, lang, key, value, mode):
        insert_dict = {'wkey':key, 'wvalue':value, 'language':lang, 'mode':mode}
        sql = insertFromDict("new_words", insert_dict)
        try:
            cursor = cherrypy.thread_data.db.cursor()
        except Exception, e:
            connect()
            cursor = cherrypy.thread_data.db.cursor()
            logger.warn(str(e))
            
        cursor.execute(sql, insert_dict)
        cursor.close()
        
def getHTML(message, lang=None, withNote=True):
    htmlMsg = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"><html><head><xmeta content="text/html;charset=utf-8" http-equiv="Content-Type"></head><xbody bgcolor="#ffffff" text="#000000"><pre>'+ message + '</pre>'
    if withNote:
        htmlMsg += '<br><p>If you are seeing junk characters instead of the correct ' + lang +' characters, in your browser go to \'View->Encoding\' and select the option \'Unicode (UTF-8)\'. To respond to this email in '+ lang +', visit http://quillpad.in/'+lang+'</p>'
        
    htmlMsg +=  '</xbody></html>'
    return htmlMsg

def getFormattedHTML(message, lang):
    htmlMsg = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"><html><head><xmeta content="text/html;charset=utf-8" http-equiv="Content-Type"></head><xbody>' + message 
    htmlMsg += '<br><p>If you are seeing junk characters instead of the correct ' + lang +' characters, in your browser go to \'View->Encoding\' and select the option \'Unicode (UTF-8)\'. To respond to this email in '+ lang +', visit http://quillpad.in/'+lang+'</p>'
    htmlMsg +=  '</xbody></html>'
    return htmlMsg


def createhtmlmail(subject, text, html, email_from, email_to, email_replyto):
    " Create a mime-message that will render as HTML or text, as appropriate"

    out = cStringIO.StringIO( )              # output buffer for our message
    htmlin = cStringIO.StringIO(html)    # input buffer for the HTML
    txtin = cStringIO.StringIO(text)     # input buffer for the plain text
    writer = MimeWriter.MimeWriter(out)
    # Set up some basic headers. Place subject here because smtplib.sendmail
    # expects it to be in the message, as relevant RFCs prescribe.
    writer.addheader("Subject", subject)
    writer.addheader("To", email_to)
    writer.addheader("MIME-Version", "1.0")
    writer.addheader("From", email_from)
    writer.addheader("Reply-To", email_replyto)
    writer.addheader("Cc", email_replyto)
    writer.addheader("Date", email.Utils.formatdate(localtime=1))
    writer.addheader("Message-ID", email.Utils.make_msgid())

    # Start the multipart section of the message.  Multipart/alternative seems
    # to work better on some MUAs than multipart/mixed.
    writer.startmultipartbody("alternative")
    writer.flushheaders( )
    # the plain-text section: just copied through, assuming iso-8859-1
    subpart = writer.nextpart( )
    #pout = subpart.startbody("text/plain", [("charset", 'iso-8859-1')])
    pout = subpart.startbody("text/plain", [("charset", 'utf-8')])
    pout.write(txtin.read( ))
    txtin.close( )
    # the HTML subpart of the message: quoted-printable, just in case
    subpart = writer.nextpart( )
    #subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    subpart.addheader("Content-Transfer-Encoding", "8bit")
    #pout = subpart.startbody("text/html", [("charset", 'us-ascii')])
    pout = subpart.startbody("text/html", [("charset", 'utf-8')])
    #mimetools.encode(htmlin, pout, 'quoted-printable')
    mimetools.encode(htmlin, pout, '8bit')
    htmlin.close( )
    # You're done; close your writer and return the message as a string
    writer.lastpart( )
    msg = out.getvalue( )
    out.close( )
    return msg
        

def insertFromDict(table, dict):
    """Take dictionary object dict and produce sql for
    inserting it into the named table"""
    sql = 'INSERT INTO ' + table
    sql += ' ('
    sql += ', '.join(dict)
    sql += ') VALUES ('
    sql += ', '.join(map(dictValuePad, dict))
    sql += ');'
    return sql

def dictValuePad(key):
    return '%(' + str(key) + ')s'

def connect(thread_index=None):
    # Create a connection and store it in the current thread
    try:
        cherrypy.thread_data.db= MySQLdb.connect(host='127.0.0.1', user='quill', passwd='quill', db='quill', charset='utf8' )
    except Exception,e:
        print e
        logger.error(str(e))

# Tell CherryPy to call "connect" for each thread, when it starts up
cherrypy.engine.subscribe('start_thread', connect)

def tupleToStrList(ustrList):
    return [x[0] for x in ustrList[1] ]

def main() :
    """
    cherrypy.root = QuillCherry()
    cherrypy.root.quillpad_backend = cherrypy.root
    cherrypy.config.update( file='quill_cherry8088.conf')
    cherrypy.config.update({'thread_pool': 10})
    cherrypy.server.start()
    """
    cherrypy._cpconfig.Config('quill_cherry8088.conf')
    quillCherry = QuillCherry()
    cherrypy.quickstart(quillCherry)

if __name__ == '__main__' :
    main()
