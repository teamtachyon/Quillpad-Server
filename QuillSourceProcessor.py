# -*- coding: utf-8 -*-
# @Date    : Jul 13, 2016
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

import QuillLanguage as qlang
import QuillEngXlit as xlit
import re
import const
import primaryHelper

class QuillSourceProcessor(object):
    def __init__(self):
        useCCart=True

        bengaliDefFile='Bengali_Vrinda.xml'
        bengaliKnowledgeInput='bengali'

        gujaratiDefFile='Gujarati_Shruti.xml'
        gujaratiKnowledgeInput='gujarati'

        hindiDefFile='Hindi_Mangal.xml'
        hindiKnowledgeInput='hindi'
        
        hindiMobileDefFile='Hindi_Mangal_Mobile.xml'
        hindiMobileKnowledgeInput='hindiMobile'
        
        kannadaDefFile='Kannada_Tunga.xml'
        kannadaKnowledgeInput='kannada'
        
        kannadaMobileDefFile='Kannada_Tunga_Mobile.xml'
        kannadaMobileKnowledgeInput='kannada_list_mobile.txt'
        
        malayalamDefFile='Malayalam_Kartika.xml'
        malayalamKnowledgeInput='malayalam'
        
        malayalamMobileDefFile='Malayalam_Kartika_Mobile.xml'
        malayalamMobileKnowledgeInput='malayalam_list_mobile.txt'
        
        marathiDefFile='Marathi_Mangal.xml'
        marathiKnowledgeInput='marathi'
        
        marathiMobileDefFile='Marathi_Mangal_Mobile.xml'
        marathiMobileKnowledgeInput='marathi_list_mobile.txt'

        nepaliDefFile='Nepali_Mangal.xml'
        nepaliKnowledgeInput='nepali'
 
        punjabiDefFile='Punjabi_Raavi.xml'
        punjabiKnowledgeInput='punjabi'
        
        tamilDefFile='Tamil_Latha.xml'
        tamilKnowledgeInput='tamil'
        
        tamilMobileDefFile='Tamil_Latha_Mobile.xml'
        tamilMobileKnowledgeInput='tamil_list_mobile.txt'
        
        teluguDefFile='Telugu_Raavi.xml'
        teluguKnowledgeInput='telugu'
        
        teluguMobileDefFile='Telugu_Raavi_Mobile.xml'
        teluguMobileKnowledgeInput='telugu_list_mobile.txt'
        
        self.scriptEngines = {'english':None,
                'bengali':qlang.QuillLanguage(bengaliDefFile,bengaliKnowledgeInput,useCCart),
                'gujarati':qlang.QuillLanguage(gujaratiDefFile,gujaratiKnowledgeInput,useCCart),
                'hindi':qlang.QuillLanguage(hindiDefFile,hindiKnowledgeInput,useCCart),
                #'hindiMobile':qlang.QuillLanguage(hindiMobileDefFile,hindiMobileKnowledgeInput,useCCart),
                'kannada':qlang.QuillLanguage(kannadaDefFile,kannadaKnowledgeInput,useCCart),
                #'kannadaMobile':qlang.QuillLanguage(kannadaMobileDefFile,kannadaMobileKnowledgeInput,useCCart),
                'malayalam':qlang.QuillLanguage(malayalamDefFile,malayalamKnowledgeInput,useCCart),
                #'malayalamMobile':qlang.QuillLanguage(malayalamMobileDefFile,malayalamMobileKnowledgeInput,useCCart),
                'marathi':qlang.QuillLanguage(marathiDefFile,marathiKnowledgeInput,useCCart),
                #'marathiMobile':qlang.QuillLanguage(marathiMobileDefFile,marathiMobileKnowledgeInput,useCCart),
                'nepali':qlang.QuillLanguage(nepaliDefFile,nepaliKnowledgeInput,useCCart),
                'punjabi':qlang.QuillLanguage(punjabiDefFile,punjabiKnowledgeInput,useCCart),
                'tamil':qlang.QuillLanguage(tamilDefFile,tamilKnowledgeInput,useCCart),
                #'tamilMobile':qlang.QuillLanguage(tamilMobileDefFile,tamilMobileKnowledgeInput,useCCart),
                'telugu':qlang.QuillLanguage(teluguDefFile,teluguKnowledgeInput,useCCart),
                #'teluguMobile':qlang.QuillLanguage(teluguMobileDefFile,teluguMobileKnowledgeInput,useCCart)
        }

        self.xlitEngines = {
                'kannada': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Kannada_Xlit.xml'),
                'bengali': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Bengali_Xlit.xml'),
                'gujarati': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Gujarati_Xlit.xml'),
                'hindi': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Hindi_Xlit.xml'),
                'marathi': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Marathi_Xlit.xml'),
                'nepali': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Nepali_Xlit.xml'),
                'punjabi': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Punjabi_Xlit.xml'),
                'telugu': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Telugu_Xlit.xml'),
                'tamil': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Tamil_Xlit.xml'),
                'malayalam': xlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Malayalam_Xlit.xml')
        }

        self.clashMaps = {
                'bengali': self.makeClashMap('bengaliClashList.txt'),
                'gujarati': self.makeClashMap('gujaratiClash.txt'),
                'hindi': self.makeClashMap('hindiClash.txt'),
                'kannada': self.makeClashMap('kannadaClash.txt'),
                'tamil': self.makeClashMap('tamilClash.txt'),
                'marathi': self.makeClashMap('marathiClash.txt'),
                'nepali': self.makeClashMap('nepaliClash.txt'),
                'punjabi': self.makeClashMap('punjabiClash.txt'),
                'telugu': self.makeClashMap('teluguClash.txt'),
                'malayalam': self.makeClashMap('malayalamClash.txt')
        }

        self.modeTypes = ['predictive','xliterate','itrans']
        
        self.inputBuffer =''
        self.outputBuffer=''
        
        self.scriptCommandRE = r"(?<!\\)\\(english|bengali|gujarati|hindi|hindiMobile|kannada|kannadaMobile|malayalam|malayalamMobile|marathi|marathiMobile|nepali|punjabi|tamil|tamilMobile|telugu|teluguMobile)" #starts with alpha followed alpha-numerics
        self.modeCommandRE = r"(?<!\\)\\(predictive|xliterate|itrans){((?:\\{|[^{}\\]|\\}|\\)*)}"
        
        self.compSC = re.compile(self.scriptCommandRE)
        self.compMC = re.compile(self.modeCommandRE)
        
        self.currLanguage = 'english'
        self.currMode = 'predictive'
        
        self.engine = None

        self.loadEnglishDict('dict.txt')

    def loadEnglishDict(self, fname):
        words = open(fname).read().split()
        self.engWords = dict([(w, None) for w in words])
        
        print "Loaded english dictionary from...", fname

    def makeClashMap(self, fname):
        words = open(fname).read().split()
        return dict([(w, None) for w in words])
    
    def processText(self,inString, onlyFirstOptions=False):
        self.inputBuffer = inString
        self.outputBuffer = ''
        index = 0
        langText=''
        while index < len(self.inputBuffer):
            scriptCmdMatch = self.compSC.match(self.inputBuffer,index)
            modeCmdMatch = self.compMC.match(self.inputBuffer,index)

            if scriptCmdMatch != None:
                self.outputBuffer += self.renderText(langText)
                langText = ''
                self.currLanguage = scriptCmdMatch.group(1)
                self.switchLanguage(self.currLanguage)
                index = scriptCmdMatch.end()

            elif modeCmdMatch != None and self.currLanguage != 'english':
                self.outputBuffer += self.renderText(langText)
                langText = ''

                mode = modeCmdMatch.group(1)
                text = modeCmdMatch.group(2)

                self.switchMode(mode)
                self.outputBuffer += self.renderText(text)
                self.switchMode('predictive')
              
                index = modeCmdMatch.end()
            else:
                langText += self.inputBuffer[index]
                index +=1
        
        self.outputBuffer += self.renderText(langText, onlyFirstOptions)
        
        return self.outputBuffer
    
    def switchMode(self,mode):
        self.currMode = mode
    
    def renderText(self,langText, onlyFirstOptions=False):
        
        index = 0
        insideWord = False
        renderedText = ''
        currWord = ''
        
        if self.engine == None:
            return langText

        if self.currMode == 'predictive' and (not onlyFirstOptions):
            convertedList = self.engine.convert(langText,"predictive", True)
            if len(convertedList) == 1:
                onlyTuple = convertedList[0]
                if type(onlyTuple[0]) == str:
                    renderedText = onlyTuple[0]
                else:
                    renderedText = const.optionSeperator.join(onlyTuple[0])
            else :
                renderedText += '----multiple----\n'
                
                for (ustr, count) in convertedList:
                    if type(ustr) == str:
                        #some char like ,.-' etc..
                        renderedText += str(ustr) + "\n"
                    else:
                        renderedText += const.langWordMark + str(const.optionSeperator).join(ustr) + "\n";
                
        elif self.currMode == 'predictive' and onlyFirstOptions:
            convertedList = self.engine.convert(langText,"predictive", True)
            for (ustr, count) in convertedList:
                if type(ustr) == str:
                    renderedText += str(ustr)
                else:
                    renderedText += ustr[0]
        elif self.currMode == 'itrans':
            convertedList = self.engine.convert(langText,"primary")
            for (uStr,count) in convertedList:
                for s in uStr :
                    renderedText += s
        elif self.currMode == 'xliterate':
            renderedText = langText

        return renderedText
    
    def switchLanguage(self,script):
        if self.scriptEngines.has_key(script):
            self.engine = self.scriptEngines[script]
        else:
            self.engine = None

    def xlit(self, inString, lang):
        if lang in self.xlitEngines:
            inString = inString.lower()
            engine = self.xlitEngines[lang]
            return {'xlitWords': engine.xliterate(inString)}
        else:
            return {'xlitWords': [inString]}

    def processString(self, inString, lang):
        def transliterate(word):
            if re.search("[a-zA-Z]+", word):
                return self.processWord(word, lang)["twords"][0]["options"][0]
            return word

        words = map(lambda x: x[0], re.findall("(([a-zA-Z]+)|([^a-zA-Z])+)", inString))
        return "".join(map(transliterate, words))

    def processReverseWord(self, uStr, lang):
        if self.scriptEngines.has_key(lang):
            engine = self.scriptEngines[lang]
            trainTuples = engine.getTrainingTuples(uStr)
            literals = [''.join(lit) for (lit,c,flags) in trainTuples]
            return literals
        else:
            return []

    def processWord(self, inString, lang):
        response = {"inString": inString, "twords": []}
        inString = inString.lower()

        
        if self.scriptEngines.has_key(lang):
            engine = self.scriptEngines[lang]
        else:
            # We don't support the language
            response["twords"].append({
                "word": True,
                "options": [inString],
                "optmap": {inString: inString.split()}
                })
            return response

        convertedList, numOptions = engine.literalToUnicode(inString, 
                "predictive", True)

        options = []
        optmap = {}
        for litList in convertedList:
            options.append("".join(litList))
            optmap["".join(litList)] = litList
        # options = ["".join([l[0] for l in litList]) for litList in convertedList]

        def dictSort(dlang, arr):
            a1 = []
            a2 = []
            for i in arr:
                if primaryHelper.isDictWord(dlang, i):
                    a1.append(i)
                else:
                    a2.append(i)
            return a1 + a2

        if (lang=="hindiMobile") or (lang=="hindi"):
            options = dictSort("hindi", options)
        else :
            options = dictSort(lang, options)

        def isNotITRANS(word):
            for i in word:
                if i in ".~^/":
                    return False
            return True

        def isNotDigit(word):
            for i in word:
                if i in "0123456789":
                    return False
            return True

        if lang in self.xlitEngines and isNotITRANS(inString) and isNotDigit(inString):
            xlitWords = self.xlitEngines[lang].xliterate(inString)

            if len(xlitWords) > 0 and len(xlitWords[0]) > 0:
                xlitWord = xlitWords[0]

                if inString in self.engWords:
                    if inString in self.clashMaps[lang]:
                        if xlitWord not in options[:4]:
                            options = options[:1] + [xlitWord] + options[1:]
                    else:
                        if xlitWord in options:
                            options.remove(xlitWord)
                        options = [xlitWord] + options
                else:
                    if xlitWord not in options[:4]:
                        options = options[:3] + [xlitWord] + options[3:]

        response["twords"].append({ 
            "word": True, 
            "options": options,
            "optmap": optmap
            })

        return response

    def getCorrections(self, lang, currWord, userInput, pos):
        if self.scriptEngines.has_key(lang):
            engine = self.scriptEngines[lang]
        else:
            return ["".join(currWord)]

        return engine.getCorrections(currWord, userInput, pos)

    def getCorrectionsStr(self, lang, currWord, userInput, pos):
        if self.scriptEngines.has_key(lang):
            engine = self.scriptEngines[lang]
        else:
            return currWord

        return engine.getCorrectionsStr(currWord, userInput, pos)


if __name__ == '__main__':
    inString = "raja-deepthi"

    proc = QuillSourceProcessor()
    proc.switchLanguage("hindi")
    out = proc.processText(inString);

    f = open('out.txt','w')
    utext= out.encode('utf-8')
    f.write(utext)
    f.close()
