# -*- coding: utf-8 -*-
# @Date    : Jan 25, 2013
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

import QuillLanguage
import QuillPrimary

import xml.etree.cElementTree as ET
import copy
import re

from optparse import OptionParser

class QuillEngXliterator(object):
    def __init__(self,knowledgeDir1,knowledgeDir2,xlitDef):
        self.directMode = False
        self.lit2engEngine = None
        self.eng2indEngine = None
        self.lit2indEngine = None
        
        if knowledgeDir1 != None and knowledgeDir2 != None:
            self.lit2engEngine = QuillLanguage.QuillLanguage(langKnowledgeInput=knowledgeDir1, useCCart = True)
            self.eng2indEngine = QuillLanguage.QuillLanguage(langKnowledgeInput=knowledgeDir2, useCCart = True)
        else:
            self.lit2indEngine = QuillLanguage.QuillLanguage(langKnowledgeInput=knowledgeDir1, useCCart = True)
            self.directMode = True
        
        self.primEngine = None
        self.xlitRules = None
        self.loadXlitRules(xlitDef)
        self.compileFeatureRes()
        
        self.debugLit = ''
    
    def codeGen(self):
        codeChars = 'abcdefghijklmnopqrstuvwxyz'
        firstIndex = 0
        secondIndex = 0 
        while firstIndex < len(codeChars) and secondIndex < len(codeChars):
            code = codeChars[firstIndex]+ codeChars[secondIndex].upper() #This will ensure that end of one code and beginning of next code, cant be another valid code! Very imp.
            secondIndex += 1
            if secondIndex == len(codeChars):
                secondIndex = 0
                firstIndex += 1  
            yield code

    def loadXlitRules(self, xlitDef):
        try:
            f = open(xlitDef,'r')
        except IOError:
            print "Can't load the language definition file"
            return

        cGen = self.codeGen()
        
        xlitTree = ET.parse(f)
        xlitRoot = xlitTree.getroot()

        primaryDef = xlitRoot.attrib['primary']
        self.primEngine = QuillPrimary.QuillRuleBased(primaryDef)
        
        self.alphabet = {}
        self.phoneme2code = {}
        self.code2phoneme = {}
        
        for tree in xlitRoot.getchildren():
            if tree.tag == 'features':
                phoneme = tree.attrib['phoneme'].strip()
                code = cGen.next()
                
                self.phoneme2code[phoneme] = code
                self.code2phoneme[code] = phoneme
                
                featuresObj = features(code)
                for feature in tree.getchildren():
                    if feature.tag == 'properties':
                        props = eval(feature.text)
                        if type(props) == str:
                            props = [props]
                        else:
                            props = list(props)
                        featuresObj.setProps(props)
                    elif feature.tag == 'producer':
                        regex = eval(feature.attrib['regex'])
                        options = eval(feature.attrib['value'])

                        featuresObj.addProducer(regex,options)
                        self.alphabet[code]=featuresObj
        f.close()

    def getCodes(self,prop):
        """Returns list of alphabet letters that satisfy this property"""
        letters =[]
        for (k,v) in self.alphabet.items():
            props = v.getProps()
            if prop in props:
                letters.append(k)
        return letters

    def compileRe(self,reStr):
        m=re.compile(r'_([^_]+)_')
        result = m.search(reStr)
        while result:
            prop = result.group(1)
            orList = self.getCodes(prop)
            orRegex = '(?:'+'|'.join(orList)+')'
            toReplace = reStr[result.start():result.end()]
            reStr = reStr.replace(toReplace,orRegex)
            result = m.search(reStr)
        
        finalRegex = reStr
        return finalRegex

    def compileFeatureRes(self):
        for f in self.alphabet.values():
            litProducers = f.getAllProducers()
            for (k,v) in litProducers:
                newRegex = self.compileRe(k)
                f.changeProducerRe(k,newRegex)

    def optionsChain(self,phonemeRepStr):
        phonesList = [x.strip() for x in phonemeRepStr.split(' ') if len(x.strip()) > 0]
        try:
            codeList = [self.phoneme2code[ph] for ph in phonesList]
        except KeyError:
            return [[]]
        
        literal = ''.join(codeList)
        chain =[[]]*len(codeList)
        
        for (index,code) in enumerate(codeList):
            f = self.alphabet[code]
            literalProducers = f.getAllProducers()
            bestMatchLen=0
            for (regStr,options) in literalProducers:
                iter = re.finditer(regStr,literal)
                for match in iter:
                    matchLen = len(match.group())
                    matchIndex = match.start(1)
                    
                    if matchLen > bestMatchLen and matchIndex == (2*index): #this ensures for equal lenght match, the match appearing first will be taken
                        chain[index] = options
                        bestMatchLen = matchLen

        return chain

    def getIndianPronunciations(self,literal):
        if self.directMode == True:
            (indPronunciations,count) = self.lit2indEngine.literalToUnicode(list(literal),multiple = True)
            
            pronunciations = []
    
            for indPronunciation in indPronunciations:
                indPronunciationStr = ' '.join([x.strip() for x in indPronunciation if x.strip() != ''])
                indPronunciationStr = indPronunciationStr.replace('er','ah r')
                indPronunciationStr = indPronunciationStr.replace('_',' ')
                indPronunciationStr = indPronunciationStr.replace('#','')
                indPronunciationStr = indPronunciationStr.replace('$','')
                
                indPronunciationStr = ' - '.join([x.strip() for x in indPronunciationStr.split('-') if x.strip() != ''])
    
                pronunciations.append(indPronunciationStr)
                
            return pronunciations
        else:
            (engPronunciation,count) = self.lit2engEngine.literalToUnicode(list(literal))
            engPronunciationStr = ' '.join(engPronunciation)
    
            for (cIndex,c) in enumerate(literal):
                if engPronunciation[cIndex] == '':
                    engPronunciation[cIndex] = '#'
                engPronunciation[cIndex] = engPronunciation[cIndex].replace(' ','_')
    
            indPronounceInput = [] 
            for (cIndex,c) in enumerate(literal):
                indPronounceInput.append('%s,%s'%(engPronunciation[cIndex],c))
                
            (indPronunciation,count) = self.eng2indEngine.literalToUnicode(indPronounceInput)
                
            indPronunciationStr = ''
            indPronunciationParts =[]
            dashAdded = False
            if count != -1:
                for (cIndex,c) in enumerate(engPronunciation):
                    indPronunciation[cIndex] = indPronunciation[cIndex].replace('_',' ')
                    if indPronunciation[cIndex].strip() == '':
                        continue
                    elif indPronunciation[cIndex][0] == '-':
                        if dashAdded == False:
                            indPronunciationParts.append('-')
                            dashAdded = True
                        if indPronunciation[cIndex][1:] != '#':
                            indPronunciationParts.append(indPronunciation[cIndex][1:])
                            dashAdded = False
                        
                    elif indPronunciation[cIndex][-1] == '-':
                        if indPronunciation[cIndex][:-1] != '#':
                            indPronunciationParts.append(indPronunciation[cIndex][:-1])
                            dashAdded = False
                        if dashAdded == False:
                            indPronunciationParts.append('-')
                            dashAdded = True
                    else:
                        if indPronunciation[cIndex] != '#':
                            indPronunciationParts.append(indPronunciation[cIndex])
                            dashAdded = False
        
                indPronunciationStr = ' '.join(indPronunciationParts)
            else:
                indPronunciationStr = self.ignoreStress(indPronunciationStr)
            
            indPronunciationStr = indPronunciationStr.replace('er','ah r')
            
            return [indPronunciationStr]

    def xliterate(self, literal):
        indPronunciations = self.getIndianPronunciations(literal)
        primStringsList = []
        for indPronunciationStr in indPronunciations:
            primStrings = self.getPrimaryStrings(indPronunciationStr)
            primStringsList.extend(primStrings)
        
        return self.xliterateInternal(primStringsList)
    
    def xliterateInternal(self, primaryStringsList):
        unicodeList = []
        for primaryStr in primaryStringsList:
            uStr = self.primEngine.primaryToUnicode(primaryStr)
            unicodeList.append(uStr)
        return unicodeList
    
    def getPrimaryStrings(self,indPronunciationStr):
        optionsChain = self.optionsChain(indPronunciationStr)

        primLitList = [[]]
        count = reduce(lambda x, y: x*y, map(len, optionsChain), 1)

        if count > 100:
            print "getPrimaryString: Permutations execeeded count. Count =", count
            return [''.join([litList[0] for litList in optionsChain])]
        else: 
            for (i,options) in enumerate(optionsChain):
                newList=[]

                for eachOption in options:
                    temp = copy.deepcopy(primLitList)
                    for x in temp:
                        x.append(eachOption)
                    newList.extend(temp)
                primLitList = newList
        
        return [''.join(litList) for litList in primLitList]

    def ignoreStress(self, pronunciation):
       stressRemoved = ''
       removeChars = '012'
       for (i,c) in enumerate(pronunciation):
           if c in removeChars:
               if i > 1 and pronunciation[i-2:i] == 'ow':
                   if c == '0':
                       continue
                   else:
                       stressRemoved += '1'
                       continue
               elif i > 0 and pronunciation[i-1].isalpha():
                   continue
           stressRemoved += c

       return stressRemoved

class features(object):
    def __init__(self,keyUnichar):
        self.key = keyUnichar
        self.props =[]
        self.literalProducers = []
        
    def addProducer(self,regexStr,outLiteralsList):
        self.literalProducers.append([regexStr,outLiteralsList])
    
    def changeProducerRe(self,oldRe,newRe):
        for prods in self.literalProducers:
            if prods[0] == oldRe:
                prods[0] = newRe
                break
    
    def getAllProducers(self):
        itemsList =[tuple(x) for x in self.literalProducers]
        return itemsList
    
    def setProps(self,properties):
        self.props = properties
    
    def getProps(self):
        return self.props
    
    def getLiterals(self,type):
        literals =[]
        for v in self.literalProducers:
            if type == 'predictive':
                options = v[1][1]
            else:
                options = v[1][0]
            for lit in options:
                if lit not in literals:
                    literals.append(lit)
        return literals
    
    def getLiteralsForPattern(self,pattern,type):
        literals =[]
        for v in self.literalProducers:
            if v[0]==pattern:
                if type == 'predictive':
                    literals = v[1][1]
                else:
                    literals = v[1][0]
                break
            
        return literals
    
    def getPatterns(self):
        patterns =[]
        for v in self.literalProducers:
            patterns.append(v[0])
        return patterns
    
    def isPropTrue(self,prop):
        return prop in self.props
    
    def allPropsTrue(self,propList):
        for prop in propList:
            if prop not in self.props:
                return False
        return True
