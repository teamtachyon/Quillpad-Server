from aifc import Error
import cherrypy
from QuillManual import QuillManual 

class QuillManualCherry:
    
    @cherrypy.expose
    def primaryToUnicodeCherry(self, literal ) :
        try:
            print "Invoking primaryToUnicode on QuillManual..."
            return literal + "\n" +  self.quillManual.primaryToUnicode( literal )
        except Exception:
            print Exception
            return "-------------";
    
    @cherrypy.expose
    def unicodeToPrimaryCherry(self, uStr ) :
        try:
            return uStr.decode('utf-8') + "\n" + self.quillManual.unicodeToPrimary( uStr.decode('utf-8') )
        except Exception:
            print Exception
            return "-------------";    
    
    @cherrypy.expose
    def unicodeToHelperStrCherry(self, uStr ) :
        try:
            return uStr.decode('utf-8') + "\n" + self.quillManual.unicodeToHelperStr( uStr.decode('utf-8') )
        except Exception:
            print Exception
            return "-------------";
    
    @cherrypy.expose
    def getOptionsAtCherry(self, currHelper, currUStr, pos ) :
        try:
            return currUStr.decode('utf-8') + "\n" + "\n".join(self.quillManual.getOptionsAt( currHelper, currUStr.decode('utf-8'), int(pos) ))
        except Exception:
            print Exception
            return "-------------";    
    
    @cherrypy.expose
    def getInsertCorrectionsCherry(self, currHelper, currUStr, pos, delta ) :
        try:
            corrections = currUStr.decode('utf-8') + "\n" + "\n".join(self.quillManual.getInsertCorrections( currHelper, currUStr.decode('utf-8'), int(pos), delta ));
            return corrections
        except Exception:
            print Exception
            return "-------------";
    
    @cherrypy.expose
    def getDeleteCorrectionsCherry(self, currHelper, currUStr, pos, delLen ) :
        try:
            return currUStr.decode('utf-8') + "\n" + "\n".join(self.quillManual.getDeleteCorrections( currHelper, currUStr.decode('utf-8'), int(pos), int(delLen) ))
        except Exception:
            print Exception
            return "-------------";

    def __init__(self):
        self.quillManual = QuillManual()
        self.quillManual.loadPrimaryDef()

def main() :
    cherrypy.root = QuillManualCherry()
    cherrypy.config.update( file='quill_manual.conf' )
    cherrypy.server.start()

if __name__ == '__main__' :
    main()
