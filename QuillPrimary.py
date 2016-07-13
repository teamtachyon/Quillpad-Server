# -*- coding: utf-8 -*-
# @Date    : Jan 25, 2013
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

import xml.etree.cElementTree as ET
import Pyrex.Plex
import StringIO
import re
import copy

class QuillRuleBased(object):
    def __init__(self,langDefFile=None,uniqueWordFile=None):
        self.codeChars = 'abcdefghijklmnopqrstuvwxyz'
        
        if langDefFile != None:
            self.loadPrimaryDef(langDefFile,uniqueWordFile)
    
    def codeGen(self):
        firstIndex = 0
        secondIndex = 0 
        count = 0
        while firstIndex < len(self.codeChars) and secondIndex < len(self.codeChars):
            code = self.codeChars[firstIndex]+ self.codeChars[secondIndex].upper()
            secondIndex += 1
            if secondIndex == len(self.codeChars):
                secondIndex = 0
                firstIndex += 1
            yield code

    def loadPrimaryDef(self,langDefFile,uniqueWordFile):
        try:
            f = open(langDefFile,'r')
        except IOError:
            print "Can't load the primary definition file"
            return False
            
        lang = ET.parse(f)
        primdef = lang.getroot()
        
        
        self.preProcs = []

        
        self.litLexicon = None
        self.codeIDLexicon = None
        
        litTokensGen = self.codeGen()
        intTokensGen = self.codeGen()
        ucodeIDGen = self.codeGen()

        self.virtualInterfaceMap = {}
        
        self.groupsMap = {}
        self.level1PropsMap = {}
        self.level0PropsMap = {}
        self.token2renderProps = {}
        self.contextsMap = {}
        self.renderRules = {}
        self.utolitRules = {}
        self.token2utolitProps = {}

        self.ucode2id = {}
        self.name2tokens = {}
        self.token2code = {}
        self.code2token = {}
        self.token2litAliases = {}
        
        self.aksharaPattern = ''
        self.simpleAkshara = ''
        
        litLexParams = []
        codeIDLexParams = []
        
        self.examplesParams = []

        for tree in primdef.getchildren():
            if tree.tag == 'CF-Mappings' or tree.tag == 'CS-Mappings':
                for mapping in tree.getchildren():
                    lit = mapping.attrib['lit']
                    aliases = eval(mapping.attrib['aliases'])
                    
                    tokenValue = litTokensGen.next()
                    self.level0PropsMap[lit] = [tokenValue]
                    
                    for alias in aliases:
                        litLexParams.append((Pyrex.Plex.Str(alias),tokenValue))
                    
                    for attributes in mapping.getchildren():
                        contextRe = attributes.attrib['context']

                        intToken = intTokensGen.next()
                        
                        self.token2litAliases[intToken] = aliases
                        
                        for attribs in attributes.getchildren():
                            name = ''
                        
                            if attribs.tag == 'group':
                                groupName = attribs.text
                                if groupName in self.groupsMap:
                                    self.groupsMap[groupName].append(intToken)
                                else:
                                    self.groupsMap[groupName] = [intToken]

                            if attribs.tag == 'prop':
                                name = attribs.attrib['name']
                                props = eval(attribs.text)
                                
                                self.name2tokens[name] = intToken
                                
                                if tokenValue in self.contextsMap:
                                    self.contextsMap[tokenValue].append((contextRe,intToken))
                                else:
                                    self.contextsMap[tokenValue] = [(contextRe,intToken)]
                                
                                for prop in props:
                                    if tree.tag == 'CF-Mappings': 
                                        if prop in self.level0PropsMap:
                                            self.level0PropsMap[prop].append(tokenValue)
                                        else:
                                            self.level0PropsMap[prop] = [tokenValue]
                                    
                                    if prop in self.level1PropsMap:
                                        self.level1PropsMap[prop].append(intToken)
                                    else:
                                        self.level1PropsMap[prop] = [intToken]
                            if attribs.tag == 'code':
                                code = eval(attribs.text)
                                self.token2code[intToken] = code
                                self.code2token[code] = intToken
                                
                                for ucode in code:
                                    if ucode not in self.ucode2id:
                                        self.ucode2id[ucode] = ucodeIDGen.next()
            
            elif tree.tag == 'render-rules':
                for rule in tree.getchildren():
                    prop = rule.attrib['prop']
                    self.renderRules[prop] = []
                    for producer in rule.getchildren():
                        reStr = producer.attrib['regex']
                        replaceStr = producer.attrib['replace']
                        self.renderRules[prop].append((reStr,replaceStr))
                    
            elif tree.tag == 'utolit-rules':
                for rule in tree.getchildren():
                    prop = rule.attrib['prop']
                    self.utolitRules[prop] = []
                    for producer in rule.getchildren():
                        reStr = producer.attrib['regex']
                        replaceStr = producer.attrib['replace']
                        self.utolitRules[prop].append((reStr,replaceStr))
 
            elif tree.tag == 'preprocessor':
                regex = eval(tree.attrib['regex'])
                value = eval(tree.attrib['value'])
                self.preProcs.append((regex,value))
            
            elif tree.tag == 'akshara':
                self.aksharaPattern = tree.attrib['regex']
            
            elif tree.tag == 'simple-akshara':
                self.simpleAkshara = tree.attrib['regex']

            elif tree.tag == 'examples':
                for example in tree.getchildren():
                    input=''
                    note =''
                    for attributes in example.getchildren():
                        if attributes.tag == 'input':
                            input = attributes.text
                        elif attributes.tag == 'note':
                            note = attributes.text

                    if input.strip() != '':
                        self.examplesParams.append((input.strip(),note.strip()))
            
        f.close()
        
        litLexParams.append((Pyrex.Plex.AnyChar,'#'))
        self.litLexicon = Pyrex.Plex.Lexicon(litLexParams)

        for (code,token) in self.code2token.items():
            if len(code) > 0:
                codeIDStr = ''
                for ucode in code:
                    codeIDStr +=  self.ucode2id[ucode]
                codeIDLexParams.append((Pyrex.Plex.Str(codeIDStr),token))
            
        codeIDLexParams.append((Pyrex.Plex.AnyChar,'#'))
        self.codeIDLexicon = Pyrex.Plex.Lexicon(codeIDLexParams)

        self.aksharaPattern = self.compileRe(self.aksharaPattern,self.level1PropsMap)
        self.aksharaPattern +='|(#.)'

        self.simpleAkshara = self.compileRe(self.simpleAkshara,self.level1PropsMap)
        self.simpleAkshara +='|(#.)'
        
        self.compileContextRes()
        self.compileRenderRuleRes()
        self.compileUtolitRuleRes()
        self.buildTokensToRenderRuleProps()
        self.buildTokensToUtolitRuleProps()
        
        self.zwjSignificant = True
        self.zwnjSignificant = True

        zwjTkn = self.name2tokens['^']
        zwnjTkn = self.name2tokens['^^']
        
        self.zwjCode = self.token2code[zwjTkn]
        self.zwnjCode = self.token2code[zwnjTkn]
        
        if 'insignificant' in self.level1PropsMap:
            insigList = self.level1PropsMap['insignificant']
            if zwjTkn  in insigList:
                self.zwjSignificant = False
            if zwnjTkn  in insigList:
                self.zwnjSignificant = False

        if uniqueWordFile:
            self.buildVirtualInterfaceMap(uniqueWordFile)
            self.buildVirtualKB()
            self.buildSchemeHelp()

        
    def compileRe(self,reStr,propsMap):
        m=re.compile(r'_([^_]+)_')
        result = m.search(reStr)

        while result:
            prop = result.group(1)
            orList = propsMap[prop]
            orRegex = '(?:'+'|'.join(orList)+')'
            toReplace = reStr[result.start():result.end()]
            reStr = reStr.replace(toReplace,orRegex)
            result = m.search(reStr)

        finalRegex = reStr
        return finalRegex

    def compileStr(self,reStr,propsMap):
        m=re.compile(r'_([^_]+)_')
        result = m.search(reStr)

        while result:
            prop = result.group(1)
            orList = propsMap[prop]
            orRegex = ''.join(orList)
            toReplace = reStr[result.start():result.end()]
            reStr = reStr.replace(toReplace,orRegex)
            result = m.search(reStr)

        finalRegex = reStr
        return finalRegex


    
    def literalPreProc(self,literal):
        procs = self.preProcs
        for (rule,subst) in procs:
            literal = re.sub(rule,subst,literal)
        
        return literal

    def compileContextRes(self):
        for (token,contextPairs) in self.contextsMap.items():
            newContextReList = []
            for (contextRe,intToken) in contextPairs:
                compiledRe = self.compileRe(contextRe,self.level0PropsMap)
                newContextReList.append((compiledRe,intToken))
            
            self.contextsMap[token] = newContextReList

    def compileRenderRuleRes(self):
        for (prop,producerPairs) in self.renderRules.items():
            newProducersList = []
            for (regStr,replStr) in producerPairs:
                compiledRegStr = self.compileRe(regStr,self.level1PropsMap)
                compiledReplStr = self.compileStr(replStr,self.level1PropsMap)
                newProducersList.append((compiledRegStr,compiledReplStr))
            
            self.renderRules[prop] = newProducersList

    def compileUtolitRuleRes(self):
        for (prop,producerPairs) in self.utolitRules.items():
            newProducersList = []
            for (regStr,replStr) in producerPairs:
                compiledRegStr = self.compileRe(regStr,self.level1PropsMap)
                compiledReplStr = self.compileStr(replStr,self.level1PropsMap)
                newProducersList.append((compiledRegStr,compiledReplStr))
            
            self.utolitRules[prop] = newProducersList

    def buildTokensToRenderRuleProps(self):
        for prop in self.renderRules.keys():
            allTokens = self.level1PropsMap[prop]
            for token in allTokens:
                self.token2renderProps[token] = prop

    def buildTokensToUtolitRuleProps(self):
        for prop in self.utolitRules.keys():
            allTokens = self.level1PropsMap[prop]
            for token in allTokens:
                self.token2utolitProps[token] = prop

    def internalLiteral(self,literal):

        strIO = StringIO.StringIO(literal)
        scanner = Pyrex.Plex.Scanner(self.litLexicon,strIO,"LitScanner")
        intLiteral = ''
        while True:
            token = scanner.read()
            
            if token[0] == None:
                break
            elif token[0] == '#':
                intLiteral += ('#'+token[1])
            else:
                intLiteral += token[0]

        return intLiteral
    
    def processIntLiteral(self,intLiteral):
        
        intTokens = [intLiteral[i:i+2] for i in range(0,len(intLiteral),2)]
        
        brokenList = []
        
        currWordTokens = []
        for token in intTokens:
            if token[0] == '#':
                if len(currWordTokens) > 0:
                    brokenList.append(currWordTokens)
                
                brokenList.append([token])
                currWordTokens = []
            else:
                currWordTokens.append(token)
        
        if len(currWordTokens) > 0:
            brokenList.append(currWordTokens)

        newBrokenList = []
        for eachWord in brokenList:
            if eachWord[0][0] <> '#':
                processedWord = []
                for (index,token) in enumerate(eachWord):
                    contextsList = self.contextsMap[token]

                    tokenStr = ''.join(eachWord)
                    bestMatchLen=0
                    currRepl = ''
                    for (regStr,repl) in contextsList:
                        if len(regStr) > 0:
                            iter = re.finditer(regStr,tokenStr)
                            for match in iter:
                                matchLen = len(match.group())
                                matchIndex = match.start(1)
                                
                                if matchLen > bestMatchLen and matchIndex == 2*index:
                                    currRepl = repl
                                    bestMatchLen = matchLen

                        elif bestMatchLen==0:
                            currRepl = repl
                            
                    processedWord.append(currRepl)
                    
                newBrokenList.append(processedWord)
            else:
                newBrokenList.append(eachWord)

        processedLiteral = ''
        for eachWord in newBrokenList:
            processedLiteral += ''.join(eachWord)
        
        return processedLiteral

    def renderLiteral(self,processedLit):
        intTokens = [processedLit[i:i+2] for i in range(0,len(processedLit),2)]
        
        brokenList = []
        
        currWordTokens = []
        for token in intTokens:
            if token[0] == '#':
                if len(currWordTokens) > 0:
                    brokenList.append(currWordTokens)
                
                brokenList.append([token])
                currWordTokens = []
            else:
                currWordTokens.append(token)
        
        if len(currWordTokens) > 0:
            brokenList.append(currWordTokens)

        newBrokenList = []
        for eachWord in brokenList:
            if eachWord[0][0] <> '#':
                processedWord = ''
                for (index,token) in enumerate(eachWord):
                    
                    renderProp = self.token2renderProps[token]
                    renderProducers = self.renderRules[renderProp]
                    
                    tokenStr = ''.join(eachWord)
                    bestMatchLen=0
                    
                    chosenRegStr = ''
                    chosenRepl = ''
                    for (regStr,repl) in renderProducers:
                        if len(regStr) > 0:
                            iter = re.finditer(regStr,tokenStr)
                            for match in iter:
                                matchLen = len(match.group())
                                matchIndex = match.start(1)
                                if matchLen > bestMatchLen and matchIndex == 2*index:
                                    chosenRepl = re.sub(r'\\1',match.group(1),repl)
                                    chosenRegStr = regStr
                                    bestMatchLen = matchLen
                                
                        elif bestMatchLen == 0:
                            chosenRepl = repl

                    processedWord += chosenRepl
                                        
                newBrokenList.append([processedWord[i:i+2] for i in range(0,len(processedWord),2)])
            else:
                newBrokenList.append(eachWord)

        renderedLiteral = ''
        for eachWord in newBrokenList:
            if eachWord[0][0] <> '#':
                for token in eachWord:
                    renderedLiteral += self.token2code[token]
            else:
                renderedLiteral += eachWord[0][1]
        
        return renderedLiteral

        
    def primaryToUnicode(self,literal):
        
        literal = self.literalPreProc(literal)
        intLiteral = self.internalLiteral(literal)
        processedIntLit = self.processIntLiteral(intLiteral)
        renderedLiteral = self.renderLiteral(processedIntLit)
    
        return renderedLiteral

    def internalUStr(self,UStr):
        
        codeIDStr = ''
        for ucode in UStr:
            if ucode in self.ucode2id:
                codeIDStr += self.ucode2id[ucode]
            else:
                codeIDStr += ('-'+ucode)
        
        strIO = StringIO.StringIO(codeIDStr)
        scanner = Pyrex.Plex.Scanner(self.codeIDLexicon,strIO,"CodeIDScanner")
        intLiteral = ''
        
        prevWasEscape = False
        while True:
            token = scanner.read()
            
            if token[0] == None:
                break
            elif token[0] == '#':
                if token[1] == '-':
                    if prevWasEscape == True:
                        intLiteral += ('#'+token[1])
                        prevWasEscape = False
                    else:
                        prevWasEscape = True
                else:
                    intLiteral += ('#'+token[1])
                    prevWasEscape = False
            else:
                intLiteral += token[0]
                prevWasEscape = False

        return intLiteral

    
    def unicodeToPrimary(self,uStr):
        
        intLiteral = self.internalUStr(uStr)
        
        intTokens = [intLiteral[i:i+2] for i in range(0,len(intLiteral),2)]
        
        brokenList = []
        currWordTokens = []
        for token in intTokens:
            if token[0] == '#':
                if len(currWordTokens) > 0:
                    brokenList.append(currWordTokens)
                
                brokenList.append([token])
                currWordTokens = []
            else:
                currWordTokens.append(token)
        
        if len(currWordTokens) > 0:
            brokenList.append(currWordTokens)       

        newBrokenList = []
        for eachWord in brokenList:
            if eachWord[0][0] <> '#':
                processedWord = ''
                for (index,token) in enumerate(eachWord):
                    
                    renderProp = self.token2utolitProps[token]
                    renderProducers = self.utolitRules[renderProp]
                    
                    tokenStr = ''.join(eachWord)
                    bestMatchLen=0
                    
                    chosenRegStr = ''
                    chosenRepl = ''
                    for (regStr,repl) in renderProducers:
                        if len(regStr) > 0:
                            iter = re.finditer(regStr,tokenStr)
                            for match in iter:
                                matchLen = len(match.group())
                                matchIndex = match.start(1)
                                if matchLen > bestMatchLen and matchIndex == 2*index: #each token is guaranteed to be of length 2. so, index in str will be 2*index in list
                                    chosenRepl = re.sub(r'\\1',match.group(1),repl)
                                    chosenRegStr = regStr
                                    bestMatchLen = matchLen
                                
                        elif bestMatchLen == 0:
                            chosenRepl = repl

                    processedWord += chosenRepl
                    
                newBrokenList.append([processedWord[i:i+2] for i in range(0,len(processedWord),2)])
            else:
                newBrokenList.append(eachWord)

        litOptions = []
        
        maxOptions = 1
        for eachWord in newBrokenList:
            if eachWord[0][0] <> '#':
                for token in eachWord:
                    aliases = self.token2litAliases[token]
                    if len(aliases) > maxOptions:
                        maxOptions = len(aliases)
                    litOptions.append(tuple(aliases))
            else:
                litOptions.append((eachWord[0][1],))
        
        possibleLiterals = []
        for count in range(maxOptions):
            newLit = ''
            for optionsTuple in litOptions:
                index = min(len(optionsTuple)-1,count)
                newLit += optionsTuple[index]
            possibleLiterals.append(newLit)

        cleanPossibles = []
        for literal in possibleLiterals:
            cleanLit = literal.replace('/','')
            if self.primaryToUnicode(literal) == uStr:
                cleanPossibles.append(str(cleanLit))
            else:
                cleanPossibles.append(str(literal))
                
        return cleanPossibles
    
    def toAksharaList(self,uStr):
        intLiteral = ''
        
        for code in uStr:
            if code in self.code2token:
                intLiteral += self.code2token[code]

        aksharaIter = re.finditer(self.aksharaPattern,intLiteral)
        aksharaList = [akshara.group() for akshara in aksharaIter if len(akshara.group())>0]
        
        aksharaTupleList = []
        for akshara in aksharaList:
            aksharaM = re.match(self.simpleAkshara,akshara)
            isSimpleFlag = False
            if aksharaM != None:
                isSimpleFlag = True

            aksharaTupleList.append((akshara,isSimpleFlag))
        
        uAksharaList = []
        for (akshara,flag) in aksharaTupleList:
            uAkshara = ''
            for token in [akshara[i:i+2] for i in range(0,len(akshara),2)]:
                uAkshara += self.token2code[token]
            
            if len(uAkshara) > 0:
                uAksharaList.append((uAkshara,flag))
        
        return uAksharaList

    def buildVirtualInterfaceMap(self,uniqueWordFile):
        
        self.mathras = []
        self.dots = []
        
        for mathraTkn in self.level1PropsMap['mathra']:
            self.mathras.append(self.token2code[mathraTkn])
        
        for dotTkn in self.level1PropsMap['dot']:
            self.dots.append(self.token2code[dotTkn])
        
        self.halanth = self.token2code[self.name2tokens['.h']]
        self.nukta = self.token2code[self.name2tokens['.x']]
        
        virtualMap = {}
        
        maxOptions = 10

        words = [(line.split('\t')[0].decode('utf-8'),int(line.split('\t')[1])) for line in open(uniqueWordFile,'r').readlines()]
        
        for (word,count) in words:
            aksharaList = self.toAksharaList(word.strip())
            prevAksRoot = "^" #beginning of the word
            for (akshara,flag) in aksharaList:
                key = akshara[0]
                if key in virtualMap:
                    keyMap = virtualMap[key]
                else:
                    virtualMap[key]={}
                    keyMap = virtualMap[key]
    
                if prevAksRoot in keyMap:
                    subMap = keyMap[prevAksRoot]
                else:
                    keyMap[prevAksRoot]={}
                    subMap = keyMap[prevAksRoot]            
    
                if akshara in subMap:
                    (currCount,currFlag) = subMap[akshara]
                    subMap[akshara] = (currCount+count,flag)
                        
                else:
                    subMap[akshara] = (count,flag)
                
                prevAksRoot = akshara

        for (key,keyMap) in virtualMap.items():
            for (prev,subMap) in keyMap.items():
                items = subMap.items()
                def comp1(item1,item2):
                    return cmp(item2[1][0],item1[1][0])

                def comp2(item1,item2):
                    return cmp(item1[0],item2[0])
                        
                items.sort(cmp=comp1)

                trimSize = min(len(items),15)
                items = items[0:trimSize]

                import math
                normalizedItems = []
                logCounts = []
                maxLogCnt = 0.1
                
                for (akshara,(count,flag)) in items:
                    logCnt = math.log10(count)
                    if logCnt > maxLogCnt:
                        maxLogCnt = logCnt
                    
                    logCounts.append(logCnt)
                    
                scale = 10/maxLogCnt
                
                i=0
                for (akshara,(count,flag)) in items:
                    normalizedItems.append((akshara,(round(scale*logCounts[i]),flag)))
                    i = i+1
                
                normalizedItems.sort(cmp=comp2)
                
                simpleList = []
                
                if self.code2token[key] in self.level1PropsMap['cons']:
                    for mathra in self.mathras:
                        simpleList.append((key+mathra,0))
                    for dot in self.dots:
                        simpleList.append((key+dot,0))
                    simpleList.append((key+self.halanth,0))
                else:
                    simpleList.append((key,0))
                    for dot in self.dots:
                        simpleList.append((key+dot,0))
                
                compoundList = []
                for (akshara,(count,flag)) in normalizedItems:
                    if flag == True:
                        for (i,(a,c)) in enumerate(simpleList):
                            if a == akshara:
                                simpleList[i] = (a,count)
                                break
                    else:
                        compoundList.append((akshara,count))

                if len(compoundList)>0:
                    self.virtualInterfaceMap[prev+'+'+key] = compoundList
                
                self.virtualInterfaceMap['#+'+key] = simpleList
        
        if 'extended' in self.level1PropsMap:
            for token in self.level1PropsMap['extended']:
                key = self.token2code[token]
                simpleList = []
                for mathra in self.mathras:
                    simpleList.append((key+mathra,0))
                for dot in self.dots:
                    simpleList.append((key+dot,0))
                simpleList.append((key+self.halanth,0))
                self.virtualInterfaceMap['#+'+key] = simpleList


    def buildVirtualKB(self):
        self.virtualKB = []
        vowels = []
        mathras = [(self.halanth,'halanth','')]
        consGroups = {}
        dots = []
        extendedCons = []
        digits = []
        for (groupID,tokensList) in self.groupsMap.items():
            repTkn = tokensList[0]
            if repTkn in self.level1PropsMap['cons']:
                extendedConsList = []
                if 'extended' in self.level1PropsMap:
                    extendedConsList = self.level1PropsMap['extended']
                if repTkn not in extendedConsList:
                    if groupID not in consGroups:
                        consGroups[groupID] = []
                    
                    for tkn in tokensList:
                        alias = self.token2litAliases[tkn][0]
                        hint ='' 
                        for x in alias:
                            if x.isalpha():
                                hint = x.lower()
                                break
                        uCode = self.token2code[tkn]
                        if len(uCode.strip())> 0:
                            consGroups[groupID].append((uCode,'cons',hint))
                else:
                    for tkn in tokensList:
                        alias = self.token2litAliases[tkn][0]
                        hint ='' 
                        for x in alias:
                            if x.isalpha():
                                hint = x.lower()
                                break
                        uCode = self.token2code[tkn]
                        if len(uCode.strip())> 0:
                            extendedCons.append((uCode,'cons',hint))

            elif repTkn in self.level1PropsMap['vowel']:
                for tkn in tokensList:
                    alias = self.token2litAliases[tkn][0]
                    hint ='' 
                    for x in alias:
                        if x.isalpha():
                            hint = x.lower()
                            break
                    uCode = self.token2code[tkn]
                    if len(uCode.strip())> 0:
                        vowels.append((uCode,'vowel',hint))

            elif repTkn in self.level1PropsMap['mathra']:
                for tkn in tokensList:
                    alias = self.token2litAliases[tkn][0]
                    hint ='' 
                    for x in alias:
                        if x.isalpha():
                            hint = x.lower()
                            break
                    uCode = self.token2code[tkn]
                    if len(uCode.strip())> 0:
                        mathras.append((uCode,'mathra',hint))

            elif repTkn in self.level1PropsMap['dot']:
                for tkn in tokensList:
                    alias = self.token2litAliases[tkn][0]
                    hint ='' 
                    for x in alias:
                        if x.isalpha():
                            hint = x.lower()
                            break
                    uCode = self.token2code[tkn]
                    if len(uCode.strip())> 0:
                        dots.append((uCode,'dot',hint))

            elif repTkn in self.level1PropsMap['digit']:
                for tkn in tokensList:
                    hint = self.token2litAliases[tkn][0][0]
                    uCode = self.token2code[tkn]
                    if len(uCode.strip())> 0:
                        digits.append((uCode,'digit',hint))
        
        if len(self.nukta) > 0:
            mathras.append((self.nukta,'nukta','x'))
            
        mathras.extend(dots)
        self.virtualKB.append(mathras)
        self.virtualKB.append(vowels)

        def comp(item1,item2):
            return cmp(item1[0],item2[0])

        consLists = consGroups.values()
        consLists.sort(cmp=comp)
        
        consLists[-1].extend(extendedCons)
        self.virtualKB.extend(consLists)
        
        self.virtualKB.append(digits)
                
    def virtualIntOptions(self,currUStr,key):
        sendBackFlag = False
        prev = '^'
        if len(currUStr) > 0:
            aksharaList = self.toAksharaList(currUStr)
            prev = aksharaList[-1][0] #last akshara
        
        vMapKey = prev+'+'+key
        vMapSimpleKey = '#+'+key
        
        row1=[]
        if vMapSimpleKey in self.virtualInterfaceMap:
            row1 = self.virtualInterfaceMap[vMapSimpleKey]
        
        row2=[]
        if vMapKey in self.virtualInterfaceMap:
            row2 = self.virtualInterfaceMap[vMapKey]
        
        if (prev[-1]==self.halanth) and (self.zwjSignificant or self.zwnjSignificant):
            sendBackFlag = True
        
        return (row1,row2,sendBackFlag)
    
    def virtualWordOptions(self,currUStr,plusStr):
        key = plusStr[0]
        wordOptions = [currUStr+plusStr]
        if self.code2token[key] in self.level1PropsMap['cons']:
            if self.zwjSignificant:
                wordOptions.append(currUStr+self.zwjCode+plusStr)
            if self.zwnjSignificant:
                wordOptions.append(currUStr+self.zwnjCode+plusStr)
        
        return wordOptions
    
    def getVirtualKB(self):
        return self.virtualKB

    def buildSchemeHelp(self):
        self.schemeTable = []
        self.examples = []
        
        vowels = []
        mathras = []
        consGroups = {}
        dots = []
        extendedCons = []
        digits = []
        halanth = []
        zwm = []

        for (groupID,tokensList) in self.groupsMap.items():
            repTkn = tokensList[0]
            if repTkn in self.level1PropsMap['cons']:
                extendedConsList = []
                if 'extended' in self.level1PropsMap:
                    extendedConsList = self.level1PropsMap['extended']
                if repTkn not in extendedConsList:
                    if groupID not in consGroups:
                        consGroups[groupID] = []
                    
                    for tkn in tokensList:
                        aliases = self.token2litAliases[tkn]
                        uCode = self.token2code[tkn]
                        if len(uCode.strip())> 0:
                            consGroups[groupID].append((uCode,','.join(aliases)))
                else:
                    for tkn in tokensList:
                        aliases = self.token2litAliases[tkn]
                        uCode = self.token2code[tkn]
                        if len(uCode.strip())> 0:
                            extendedCons.append((uCode,','.join(aliases)))

            elif repTkn in self.level1PropsMap['vowel']:
                for tkn in tokensList:
                    aliases = self.token2litAliases[tkn]
                    uCode = self.token2code[tkn]
                    if len(uCode.strip())> 0:
                        vowels.append((uCode,','.join(aliases)))

            elif repTkn in self.level1PropsMap['mathra']:
                for tkn in tokensList:
                    aliases = self.token2litAliases[tkn]
                    uCode = self.token2code[tkn]
                    if len(uCode.strip())> 0:
                        mathras.append((uCode,','.join(aliases)))

            elif repTkn in self.level1PropsMap['dot']:
                for tkn in tokensList:
                    aliases = self.token2litAliases[tkn]
                    uCode = self.token2code[tkn]
                    if len(uCode.strip())> 0:
                        dots.append((uCode,','.join(aliases)))

            elif repTkn in self.level1PropsMap['digit']:
                for tkn in tokensList:
                    aliases = self.token2litAliases[tkn][0][0]
                    uCode = self.token2code[tkn]
                    if len(uCode.strip())> 0:
                        digits.append((uCode,','.join(aliases)))
        
        
        self.schemeTable.append(("Vowels", ['', ''], vowels))

        ka = self.primaryToUnicode('ka')
        kRRi = self.primaryToUnicode('kRRi')
        RRi = kRRi[-1]
        
        ra = self.primaryToUnicode('ra')
        Sha = self.primaryToUnicode('Sha')
        Ta = self.primaryToUnicode('Ta')
        shtra = self.primaryToUnicode('ShTra')
        
        ksha = self.primaryToUnicode('kSha')
        kshe = self.primaryToUnicode('kShE')
        eMathra = kshe[-1]
        
        note  = u'Mathras are joined with base consonants or conjuncts to complete a composite letter'
        ex = [u'%s + %s = %s' %(ka,RRi,kRRi), '%s + %s = %s' % (ksha,eMathra,kshe)]
        self.schemeTable.append(("Mathras", [note, ex], mathras))

        note = u'Bindus are used with consonants and conjuncts'
        ex = [u'%s + %s = %s'%(self.primaryToUnicode('ko'),self.primaryToUnicode('.n'),self.primaryToUnicode('ko.n'))]
        self.schemeTable.append(("Anusvara,Visarga and Bindus", [note, ex], dots))

        def comp(item1,item2):
            return cmp(item1[0],item2[0])

        consLists = consGroups.values()
        consLists.sort(cmp=comp)

        self.schemeTable.append(("Consonants",['',''],consLists))
        
        self.schemeTable.append(("Extended Consonants (Defined for convenience)",['', ''],extendedCons))

        if len(self.halanth) > 0:
            note1 = u'Halanth is used to combine two consonants to form conjuncts'
            ex = [u'%s +%s+ %s = %s' % (ka,self.halanth,Sha,ksha), u'%s +%s+ %s + %s + %s = %s' % (Sha,self.halanth,Ta,self.halanth,ra,shtra)]
            note2 = u'Halanth is also used to form half-consonants. %s + %s = %s'%(ka,self.halanth,ka+self.halanth)
            self.schemeTable.append(('Halanth',[note1, ex, note2],[(self.halanth,'.h')]))
        else:
            self.schemeTable.append(('Halanth',['', ''],[(self.halanth,'.h')]))

        if len(self.nukta) > 0:
            note = u'Nukta is added after a base consonant.<BR>'
            ex = u'%s +%s = %s'%(ka,self.nukta,ka+self.nukta)
            self.schemeTable.append(('Nukta',[note, ex],[(self.nukta,'.x')]))
        else:
            self.schemeTable.append(('Nukta',['', ''],[(self.nukta,'.x')]))
        
        if self.zwjSignificant:
            zwm.append(('&lt; zwj &gt;','^'))
        
        if self.zwnjSignificant:
            zwm.append(('&lt;zwnj&gt;','^^'))
            zwm.append(('&lt;delim&gt;','/'))
            
            note = u'zwj and zwnj are used to prevent default joining of two consonants.'
            ex = [u'%s + %s + %s = %s (Default)'%(ka,self.halanth,Sha,ksha),
                u'%s + %s + &lt;zwj&gt; + %s = %s (Combined with zwj)'%(ka,self.halanth,Sha,self.primaryToUnicode('k.h^Sha')),
                u'%s +%s+ &lt;zwnj&gt; + %s = %s (Combined with zwnj)'%(ka,self.halanth,Sha,self.primaryToUnicode('k.h^^Sha'))]
            note2 = u'&lt;delim&gt; has been provided as a shortcut to &lt;halanth&gt;&lt;zwnj&gt;. Look at the examples table below for further information'
        
        if len(zwm) > 0:
            self.schemeTable.append(('Zero Width Modifiers',[note, ex, note2],zwm))

        self.schemeTable.append(('Digits',['', ''],digits))
        
        for (input,note) in self.examplesParams:
            output = self.primaryToUnicode(input)
            self.examples.append((input,output,note))

    def getSchemeHelp(self):
        return (self.schemeTable,self.examples)
    
    def dumpAksharaPattern(self):
        pattern = self.aksharaPattern
        
        matchP= r'([a-z][A-Z])'
        
        iter = re.finditer(matchP,pattern)
        
        dumpablePattern =''
        prevEnd = 0
        for match in iter:
            token = match.group(1)
            (begin,end) = match.span()
            dumpablePattern += pattern[prevEnd:begin]
            dumpablePattern += self.token2code[token]
            prevEnd = end
        
        dumpablePattern += pattern[prevEnd:]
        
        return dumpablePattern
