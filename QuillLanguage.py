# -*- coding: utf-8 -*-
# @Date    : Jan 25, 2013
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

import os
import re
import copy
import xml.etree.cElementTree as ET
import Pyrex.Plex
import StringIO

from CART import CARTWord
from CART import CART
from CART import splitRule

from QuillCCart import QuillCKnowledge

class QuillLanguage(object):
    def __init__(self, langDefFile=None, langKnowledgeInput=None, useCCart = False):
        self.specialRules = []
        self.preProcs = []

        self.alphabet = {}
        self.keyToCARTMap = {}

        self.langDict = {}
        self.inputEncodeMap = {}

        self.altMap = {} 

        self.language = ''
        self.script = ''
        self.epsilon = u'\ue000'

        self.epsilon = u'\u0c81'

        self.default_font = ''

        self.useCCart = useCCart

        self.literalLexicon = Pyrex.Plex.Lexicon([])

        self.wordValidatorPattern = None
        self.wordValidatorRe = None

        if langDefFile != None:
            self.loadLanguageDef(langDefFile)
            self.compileFeatureRes()
            self.wordValidatorRe = self.compileRe(self.wordValidatorPattern)

        if langKnowledgeInput != None:
            self.loadKnowledge(langKnowledgeInput)
            self.loadAltMap()

    def literalToUnicode(self, literalList, typeStr="predictive", multiple=False, optionsAt=None):
        if ( (self.useCCart is False) and (len(self.keyToCARTMap) == 0) ):
            return (literalList, -1)

        if typeStr == "predictive":

            uLiteralChain = []
            focus = 0
            literal = ''
            encodedLiteralList  = []
            if len(self.inputEncodeMap) == 0:
                literal = self.literalPreProc(''.join(literalList).lower())
                encodedLiteralList = list(literal)
            else:
                try:
                    encodedLiteralList = [self.inputEncodeMap[x] for x in literalList]
                    literal = ''.join(encodedLiteralList)
                except KeyError:
                    if multiple == False:
                        return (literalList, -1)
                    else:
                        return ([literalList], -1)

            if literal in self.langDict:
                if multiple == False:
                    return (self.langDict[literal], 1)
                return ([self.langDict[literal]], 1)

            for code in encodedLiteralList:
                c = code[0] 
                if (self.useCCart is True ) or (c in self.keyToCARTMap.keys() ) :
                    keyCART = None;
                    if self.useCCart is False :
                        keyCART = self.keyToCARTMap[c]
                    cWord = CARTWord(literal, focus)
                    if optionsAt == focus:
                        if self.useCCart is True :
                            uLiteralChain.append( self.cCart.GetClass(literal, focus, 'predictive', False) )
                        else :
                            uLiteralChain.append(keyCART.letterToClassID(cWord, False))
                    else:
                        if self.useCCart is True :
                            uLiteralChain.append( self.cCart.GetClass(literal, focus, 'predictive', True))
                        else :
                            uLiteralChain.append(keyCART.letterToClassID(cWord, True))
                else:
                    uLiteralChain.append([('', 1.0)])

                focus += len(code)

            uLitList = [[]]
            count = reduce(lambda x, y: x*y, map(len, uLiteralChain), 1)

            if count > 100:
                print "Permutations exceeded. Count = %d." % count
                uLitList[0] = map(lambda x: x[0], uLiteralChain)
                count = 1
            else:
                for options in uLiteralChain:
                    newList=[]

                    for eachOption in options:
                        temp = copy.deepcopy(uLitList)
                        for x in temp:
                            x.append(eachOption[0])
                        newList.extend(temp)
                    uLitList = newList

            unicodeCharListOfList = [self.removeEpsilons(uLitSingle) for uLitSingle in uLitList]
            validOutput =[]
            for charList in unicodeCharListOfList:
                if (self.isValidWord("".join(charList))) == True:
                    validOutput.append(charList)
                else:
                    count = count -1 
            if count == 0:
                return (unicodeCharListOfList[0:1], 0)
            if multiple == False :
                return ( validOutput[0], count )
            return (validOutput, count)

    def loadLanguageDef(self, langDefFile):
        try:
            f = open(langDefFile, 'r')
        except IOError:
            print "Can't load the language definition file"
            return

        lang = ET.parse(f)
        quillLang = lang.getroot()
        quillLangAttrib = quillLang.attrib

        self.language = quillLangAttrib['lang']
        self.script = quillLangAttrib['script']
        self.epsilon = eval(quillLangAttrib['epsilon'])
        self.default_font = quillLangAttrib['deffont']

        self.preProcs = []
        self.alphabet = {}

        for tree in quillLang.getchildren():
            if tree.tag == 'preprocessor':
                typeStr = tree.attrib['type']
                regex = eval(tree.attrib['regex'])
                value = eval(tree.attrib['value'])
                if typeStr == "predictive":
                    self.preProcs.append((regex, value))
                elif typeStr == "primary":
                    self.preProcsPrimary.append((regex, value))

            if tree.tag == 'valid-word-pattern':
                self.wordValidatorPattern = eval(tree.attrib['regex'])

            if tree.tag == 'features':
                ucode = eval(tree.attrib['unicode'])

                featuresObj = features(ucode)
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

                        featuresObj.addProducer(regex, options)
                        self.alphabet[ucode]=featuresObj

    def loadAltMap(self):
        keys = self.cCart.GetAllCartKeys()
        for key in keys:
            classesList = self.cCart.GetAllClasses(key)
            key = chr(key)
            items = classesList.items()
            items.sort(cmp=lambda x, y:cmp(y, x), key=lambda x:x[1])

            self.altMap[key] = [x.decode('utf-8') for (x, y) in items]

    def getCorrections(self, currWord, userInput, focus):
        (pInput, pFocus) = self.getProcessedInputFocus(userInput, focus)

        key = pInput[pFocus]
        allClasses = self.altMap[key]
        altWords = []
        for alternative in allClasses:
            if alternative == self.epsilon:
                alternative = ''

            sampleWord = currWord[:]
            sampleWord[pFocus] = alternative

            if self.isValidWord(''.join(sampleWord)):
                trainTuples = self.getTrainingTuples(''.join(sampleWord))
                inputLiterals = [''.join(lit) for (lit, c, flags) in trainTuples]
                if pInput in inputLiterals:
                    altWords.append(sampleWord)

        if len(altWords) == 0 or currWord not in altWords:
            altWords = [currWord]

        return altWords

    def getCorrectionsStr(self, currWordStr, userInput, focus):
        trainTuples = self.getTrainingTuples(currWordStr)
        
        for (litList, charList, flags) in trainTuples:
            if "".join(litList) == userInput:
                charList = self.removeEpsilons(charList)
                return self.getCorrections(charList, userInput, focus)

        return [self.removeEpsilons(trainTuples[0][1])]

    def loadKnowledge(self, knowledgeDir):
        if self.useCCart :
            filesList = []
            for knowledgeFile in os.listdir( knowledgeDir ) :
                try:
                    fileName = os.path.join( knowledgeDir, knowledgeFile )
                    if os.path.isfile(fileName) and (knowledgeFile.split('.')[-1].strip()=="xml") :
                        filesList.append(fileName + '\n')
                    elif os.path.isfile(fileName) and (knowledgeFile.split('.')[-1].strip()=="dct") :
                        dictFile = fileName
                        try:
                            for line in open(dictFile).readlines():
                                [word, phonemes] = line.strip().split(' ', 1)
                                phonemes = [x.strip() for x in phonemes.split() if x.strip() != '']
                                for (i, x) in enumerate(phonemes):
                                    if x == '#':
                                        phonemes[i] = ''
                                self.langDict[word] = phonemes
                        except IOError:
                            self.langDict = {}
                    elif os.path.isfile(fileName) and (knowledgeFile.split('.')[-1].strip()=="map") :
                        try:
                            symbolsMap = open(fileName, 'r')
                            lines = symbolsMap.readlines()
                            if len(lines) > 0:
                                self.inputEncodeMap = eval(lines[0].strip())
                            symbolsMap.close()
                        except IOError:
                            self.inputEncodeMap = {}
                    else:
                        continue
                except IOError:
                    print "Can't load the knowledge file"
                    return
            import time

            tempKnowledgeFileName = knowledgeDir+'-TempKnowledgeFilesList.ls'
            tempKnowledgeFile= open(tempKnowledgeFileName, 'w')
            tempKnowledgeFile.writelines(filesList)
            tempKnowledgeFile.close()

            self.cCart = QuillCKnowledge( tempKnowledgeFileName )

            try:
                os.unlink(tempKnowledgeFileName)
            except OSError:
                pass

            return

        def makeNode(key, xmlNode):
            nodeId = int(xmlNode.attrib['id'])
            nodeProps = xmlNode.getchildren()
            splitRuleParams = nodeProps[0].getchildren()
            relIndex = int(splitRuleParams[0].text)
            contextId = int(splitRuleParams[1].text)
            contextFeatures = eval(splitRuleParams[2].text)
            spltRule = splitRule(relIndex, contextId, contextFeatures)

            cLen = int(nodeProps[1].text)
            terminalStatus = nodeProps[2].text == 'True'
            classesRep = nodeProps[3].text
            classes = ''
            if terminalStatus == True:

                classes =eval(classesRep) 

                l=[]
                for x in classes:
                    t=[]
                    for y in x:
                        if type(y) is str:
                            y = y.decode('utf-8')
                        t.append(y)
                    l.append(tuple(t))

                classes = l

            cartNode = CART(key)
            cartNode.setCARTNode(key, nodeId, cLen, spltRule, terminalStatus, classes)
            return cartNode

        nodeCount = 0
        for knowledgeFile in os.listdir( knowledgeDir ) :
            try:
                fileName = os.path.join( knowledgeDir, knowledgeFile )
                if os.path.isfile(fileName) and (knowledgeFile.split('.')[-1].strip()=="xml") :
                    f = open( fileName )
                elif os.path.isfile(fileName) and (knowledgeFile.split('.')[-1].strip()=="dct") :
                    dictFile = fileName
                    try:
                        for line in open(dictFile).readlines():
                            [word, phonemes] = line.strip().split(' ', 1)
                            phonemes = [x.strip() for x in phonemes.split() if x.strip() != '']
                            for (i, x) in enumerate(phonemes):
                                if x == '#':
                                    phonemes[x] = ''
                            self.langDict[word] = phonemes
                    except IOError:
                        self.langDict = {}
                elif os.path.isfile(fileName) and (knowledgeFile.split('.')[-1].strip()=="map") :
                    symbolsMap = open(fileName, 'r')
                    lines = symbolsMap.readlines()
                    if len(lines) > 0:
                        self.inputEncodeMap = eval(lines[0].strip())
                    symbolsMap.close()
                else:
                    continue
            except IOError:
                print "Can't load the knowledge file"
                return

            lang = ET.parse(f)
            quillLang = lang.getroot()
            quillLangAttrib = quillLang.attrib

            self.language = quillLangAttrib['lang']
            self.script = quillLangAttrib['script']
            self.epsilon = quillLangAttrib['epsilon']
            self.default_font = quillLangAttrib['deffont']

            for tree in quillLang.getchildren():
                key = tree.attrib['key']
                treeType = tree.attrib['type']
                nodes = tree.getchildren()
                keyCart = makeNode(key, nodes[0])
                nodeCount += 1
                for node in nodes[1:]:
                    cartNode = makeNode(key, node)
                    keyCart.addBinaryNode(cartNode)
                    nodeCount += 1
                if treeType == "primary":
                    self.keyToCARTMapPrimary.update({key:keyCart})
                elif treeType == "predictive":
                    self.keyToCARTMap.update( {key:keyCart } )

            f.close()

    def getValidWords(self, uText):
        matchIter = re.finditer(self.wordValidatorRe, uText)
        validWords = []
        for matchObj in matchIter:
            word = matchObj.group()
            validWords.append(word)

        return validWords

    def isValidWord(self, uWordStr):
        if self.wordValidatorRe == None:
            return True

        matchObj = re.match(self.wordValidatorRe, uWordStr)
        if matchObj == None:
            return False
        else:
            if matchObj.end() != len(uWordStr):
                return False
            else:
                return True

    def setKnowledge(self, cartMap, treeType="predictive"):
        if treeType == "primary":
            self.keyToCARTMapPrimary = cartMap
        elif treeType == "predictive":
            self.keyToCARTMap = cartMap

    def setAlphabet(self, alphaDict):
        self.alphabet = alphaDict
        self.compileFeatureRes()

    def setLexicons(self):
        symbolMap = {}
        symbolMapPrimary = {}
        for feature in self.alphabet.values():
            patterns = feature.getPatterns()
            for pattern in patterns:
                literals = feature.getLiteralsForPattern(pattern, 'predictive')
                for litStr in literals:
                    if litStr != '':
                        symbolMap[litStr] = True

        symbolKeys = symbolMap.keys()
        validSymbolsStr = 'Pyrex.Plex.Str("'+'", "'.join(symbolKeys)+'")' 

        validWordUnit = eval(validSymbolsStr)

        wordLit = Pyrex.Plex.Rep1(validWordUnit)

        nonWordChar = Pyrex.Plex.AnyChar

        userChoiceStr = wordLit + Pyrex.Plex.Str("[")

        self.literalLexicon = Pyrex.Plex.Lexicon([(userChoiceStr, Pyrex.Plex.Begin("Choice")), Pyrex.Plex.State("Choice", [(Pyrex.Plex.Str("]"), Pyrex.Plex.Begin('')), (wordLitP, "UserChoice"), (Pyrex.Plex.AnyChar, Pyrex.Plex.IGNORE)]), (wordLit, "WordLit"), (nonWordChar, "NonWordChar")]) 

    def literalPreProc(self, literal, typeStr="predictive"):

        procs = self.preProcs
        if typeStr == "primary":
            procs = self.preProcsPrimary
        for (rule, subst) in procs:
            literal = re.sub(rule, subst, literal)

        return literal

    def getProcessedInputFocus(self, userInput, focus):
        procs = self.preProcs
        pInput = userInput
        pFocus = focus

        for (rule, subst) in procs:
            substLen = len(subst)
            iter = re.finditer(rule, pInput)
            for m in iter:
                (start, stop)= m.span()
                if pFocus >= start and pFocus < stop:
                    pFocus = start+substLen-1 
                elif pFocus >= stop:
                    pFocus = pFocus - ((stop-start) - substLen)

                pInput = list(pInput)
                pInput[start:stop] = subst
                pInput = ''.join(pInput)

        return (pInput, pFocus)

    def getLetters(self, prop):
        """Returns list of alphabet letters that satisfy this property"""
        letters =[]
        for (k, v) in self.alphabet.items():
            props = v.getProps()
            if prop in props:
                letters.append(k)
        return letters

    def getFeatures(self, key):
        return self.alphabet[key]

    def getSpecialRules(self, type):
        if type == 'predictive':
            if len(self.specialRules) == 0:
                self.specialRules = self.buildSpecialRules(type)
            return self.specialRules
        if type == 'primary':
            if len(self.specialRulesPrimary) == 0:
                self.specialRulesPrimary = self.buildSpecialRules(type)
            return self.specialRulesPrimary

    def compileRe(self, reStr):
        m=re.compile(r'_([^_]+)_')
        result = m.search(reStr)
        while result:
            prop = result.group(1)
            orList = self.getLetters(prop)
            orRegex = '(?:'+'|'.join(orList)+')'
            toReplace = reStr[result.start():result.end()]
            reStr = reStr.replace(toReplace, orRegex)
            result = m.search(reStr)

        finalRegex = reStr
        return finalRegex

    def compileFeatureRes(self):
        for f in self.alphabet.values():
            litProducers = f.getAllProducers()
            for (k, v) in litProducers:
                newRegex = self.compileRe(k)
                f.changeProducerRe(k, newRegex)

    def buildSpecialRules(self, type):
        props = {}
        for (k, v) in self.alphabet.items():

            pset = v.getProps()
            for prop in pset:
                props.update({prop:{}})

        splRules=[] 
        for prop in props.keys():
            keys = self.getLetters(prop)
            rule=[]
            for key in keys:
                f = self.alphabet[key]
                v = f.getLiterals(type)
                rule.extend(v[:])

            deduper ={}
            for lit in rule:
                deduper.update({lit:lit})

            rule = deduper.keys()    
            rule.extend(["(S)Is "+prop+" ?"])

            splRules.append(rule)

        return splRules

    def getIndexablePairForPair(self, literal, uWord):
        literalChainTuple = self.allLiteralsChain(uWord)
        possibleList = self.flattenLitChainPair(literalChainTuple)
        pair = ([], [])
        for (lit, uChars) in possibleList:
            if ''.join(lit).strip() == literal.strip():
                pair = (lit, uChars)
                break
        (lit, uChars) = pair
        flatLit =[]
        flatUChars =[]
        for (i, x) in enumerate(lit):
            flatUChars.append(uChars[i])
            if len(x) > 1:
                flatLit.extend(x)
                for j in range(len(x)-1):
                    flatUChars.append(self.epsilon)
            else:
                flatLit.append(x)

        if len(flatLit) == 0 or len(flatUChars) == 0:
            flatLit = []
            flatLit.extend(literal)
            flatUChars = []
            flatUChars.extend(uWord) 

            litLen = len(flatLit)
            uLen = len(flatUChars)

            if uLen > litLen:
                flatLit.extend([self.litEpsilon]*(uLen-litLen))
            elif litLen > uLen:
                flatUChars.extend([self.epsilon]*(litLen - uLen))

        return (flatLit, flatUChars)

    def getTrainingTuples(self, uWord, treeType="predictive", charList=None):
        literalChainTuple = self.allLiteralsChain(uWord, treeType)
        possibleList = self.flattenLitChainPair(literalChainTuple)
        normalizedList = self.normalizeTrainList(possibleList, charList)
        return normalizedList

    def allLiteralsChain(self, uWord, treeType="predictive"):
        uCharList = list(uWord)
        chain =[[]]*len(uWord)
        for (index, uChar) in enumerate(uCharList):
            f = self.getFeatures(uChar)
            literalProducers = f.getAllProducers()
            bestMatchLen=0
            for (regStr, optionsTuple) in literalProducers:
                if treeType == 'predictive':
                    options = optionsTuple[1]
                elif treeType == 'primary':
                    options = optionsTuple[0]

                iter = re.finditer(regStr, uWord)
                for match in iter:
                    matchLen = len(match.group())
                    matchIndex = match.start(1)

                    if matchLen > bestMatchLen and matchIndex == index: 
                        chain[index] = options
                        bestMatchLen = matchLen
        return (uCharList, chain)

    def flattenLitChainPair(self, literalChainTuple):
        (uCharList, chain) = literalChainTuple
        possibleList = [([], [])] 
        for (i, uChar) in enumerate(uCharList):
            newList=[]
            for lit in chain[i]:
                temp = copy.deepcopy(possibleList)
                for (x, y) in temp:
                    x.append(lit)
                    y.append(uChar)
                newList.extend(temp)
            possibleList = newList
        return possibleList

    def normalizeTrainList(self, possibleList, charList = None): 
        normalizedList =[]
        for (literal, uList) in possibleList:
            newTuple = ([], [])
            for (i, c) in enumerate(literal):
                if c.strip() == '':
                    newTuple[1][-1] += uList[i]
                else:
                    newTuple[0].append(c)
                    newTuple[1].append(uList[i])

            finalTuple = ([], [], [])
            for (i, cgrp ) in enumerate(newTuple[0]):
                finalTuple[0].extend(list(cgrp))
                finalTuple[1].append(newTuple[1][i])
                finalTuple[2].extend([True]*len(cgrp))
                for i in range(1, len(cgrp)):
                    finalTuple[1].append(self.epsilon)

                if charList != None:
                    for (i, c) in enumerate(finalTuple[0]):
                        if (c in charList) == False:
                            finalTuple[2][i] = False

            normalizedList.append(finalTuple)

        return normalizedList

    def removeEpsilons(self, strList):
        assert(type(self.epsilon) is unicode)

        outStrList = []

        for s in strList:
            if s == self.epsilon:
                outStrList.append('')
            else:
                outStrList.append(s)

        return outStrList

class features(object):
    def __init__(self, keyUnichar):
        self.key = keyUnichar
        self.props =[]
        self.literalProducers = []

    def addProducer(self, regexStr, outLiteralsList):
        self.literalProducers.append([regexStr, outLiteralsList])

    def changeProducerRe(self, oldRe, newRe):

        for prods in self.literalProducers:
            if prods[0] == oldRe:
                prods[0] = newRe
                break

    def getAllProducers(self):
        itemsList =[tuple(x) for x in self.literalProducers]
        return itemsList

    def setProps(self, properties):
        self.props = properties

    def getProps(self):
        return self.props

    def getLiterals(self, type):
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

    def getLiteralsForPattern(self, pattern, type):
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

    def isPropTrue(self, prop):
        return prop in self.props

    def allPropsTrue(self, propList):
        for prop in propList:
            if prop not in self.props:
                return False
        return True
