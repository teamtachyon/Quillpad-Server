# -*- coding: utf-8 -*-
# @Date    : Jan 25, 2013
# @Author  : Ram Prakash
# @Version : 1

import QuillManual

staticQuillManual = QuillManual.QuillManual()
staticQuillManual.loadPrimaryDef()

def LoadPrimaryDef( primaryDefFile ) :
    staticQuillManual.loadPrimaryDef( primaryDefFile )

def PrimaryToUnicode( literal ) :
    return staticQuillManual.primaryToUnicode( literal )

def UnicodeToPrimary( uStr ) :
    return staticQuillManual.unicodeToPrimary( uStr.decode('utf-8') )

def UnicodeToHelperStr( uStr ) :
    return staticQuillManual.unicodeToHelperStr( uStr.decode('utf-8') )

def GetOptionsAt( currHelper, currUStr, pos ) :
    return staticQuillManual.getOptionsAt( currHelper, currUStr.decode('utf-8'), pos )

def GetInsertCorrections( currHelper, currUStr, pos, delta ) :
    corrections = staticQuillManual.getInsertCorrections( currHelper, currUStr.decode('utf-8'), pos, delta )
    return corrections

def GetDeleteCorrections( currHelper, currUStr, pos, delLen ) :
    corrections = staticQuillManual.getDeleteCorrections( currHelper, currUStr.decode('utf-8'), pos, delLen )
    return corrections
