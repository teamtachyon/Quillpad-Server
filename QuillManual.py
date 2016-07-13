# -*- coding: utf-8 -*-
# @Date    : Jan 25, 2013
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

import xml.etree.cElementTree as ET
import Pyrex.Plex
import StringIO
import re
import copy

class QuillManual(object):
	def __init__(self, langDefFile):
		self.codeChars = 'abcdefghijklmnopqrstuvwxyz'
		
		if langDefFile != None:
			self.loadPrimaryDef(langDefFile)
	
	def codeGen(self):
		firstIndex = 0
		secondIndex = 0 
		while firstIndex < len(self.codeChars) and secondIndex < len(self.codeChars):
			code = self.codeChars[firstIndex]+ self.codeChars[secondIndex].upper()
			secondIndex += 1
			if secondIndex == len(self.codeChars):
				secondIndex = 0
				firstIndex += 1  
			yield code

	def loadPrimaryDef(self, langDefFile):
		try:
			f = open(langDefFile, 'r')
		except IOError:
			print "Can't load the primary definition file"
			return False
			
		print "Loading .. " + langDefFile
		lang = ET.parse(f)
		primdef = lang.getroot()
		
		cGen = self.codeGen()
		self.preProcs = []
		self.propsMap = {}
		self.lit2token = {}
		self.token2code = {}
		self.code2token = {}
		self.token2lit = {}		
		self.lexicon = None
		self.helperLexicon = None
		for tree in primdef.getchildren():
			if tree.tag == 'codemap':
				lexiconParams = []
				for mapping in tree.getchildren():
				    lit = mapping.attrib['name']
				    code = eval(mapping.attrib['code'])
				    prop = mapping.attrib['prop']
				    litToken = cGen.next()
				    
				    if self.lit2token.has_key(lit):
				    	print "Duplicate lit name"
				    	assert(False)
				    else:
				    	self.lit2token[lit] = litToken
				    	self.token2lit[litToken] = lit
				    	lexiconParams.append((Pyrex.Plex.Str(lit), litToken))
				    	self.propsMap[lit] = [litToken]
				    	
				    self.token2code[litToken] = code
				    self.code2token[code] = litToken
				    
				    if self.propsMap.has_key(prop) == True:
				    	self.propsMap[prop].append(litToken)
				    else:
				    	self.propsMap[prop] = [litToken]
				lexiconParams.append((Pyrex.Plex.AnyChar, '#'))
				self.lexicon = Pyrex.Plex.Lexicon(lexiconParams)
			
			elif tree.tag == 'render-rules':
				self.renderRules = {}
				for rule in tree.getchildren():
					lit = rule.attrib['lit']
					token = self.compileStr(lit)
					self.renderRules[token] = []
					for producer in rule.getchildren():
						reStr = producer.attrib['regex']
						replaceStr = producer.attrib['replace']
						reStrC = self.compileRe(reStr)
						replaceC = self.compileStr(replaceStr)
						self.renderRules[token].append((reStrC, replaceC))
			elif tree.tag == 'utolit-rules':
				self.utolitRules = {}
				for rule in tree.getchildren():
					lit = rule.attrib['unicode']
					token = self.compileStr(lit)
					self.utolitRules[token] = []
					for producer in rule.getchildren():
						reStr = producer.attrib['regex']
						replaceTuple = eval(producer.attrib['replace'])
						reStrC = self.compileRe(reStr)
						replaceC = ''
						for t in replaceTuple:
							replaceC += self.lit2token[t]
						self.utolitRules[token].append((reStrC, replaceC))
			elif tree.tag == 'akshara':
				aksharaPatternStr = tree.attrib['regex']
				self.aksharaPattern = self.compileRe(aksharaPatternStr)
				self.aksharaPattern +='|(#.)'

			elif tree.tag == 'helper-groups':
				self.helperRules = {}
				self.primary2helper = {}
				lexiconParams = []
				for helper in tree.getchildren():
					key = helper.attrib['key']
					regex = helper.attrib['regex']
					options = eval(helper.attrib['options'])
					self.helperRules[key] = (regex, options)
					lexiconParams.append((Pyrex.Plex.Str(key), Pyrex.Plex.TEXT))
					for opt in options:
						if self.primary2helper.has_key(opt) == False:
							self.primary2helper[opt] = key
				
				lexiconParams.append((Pyrex.Plex.AnyChar, Pyrex.Plex.TEXT))
				self.helperLexicon = Pyrex.Plex.Lexicon(lexiconParams)
			
			elif tree.tag == 'preprocessor':
				regex = eval(tree.attrib['regex'])
				value = eval(tree.attrib['value'])
				self.preProcs.append((regex, value))

		f.close()
		
	def compileStr(self, litstr):
		m=re.compile(r'_([^_]+)_')
		result = m.search(litstr)
		while result:
			lit = result.group(1)
			token = self.lit2token[lit]
			toReplace = litstr[result.start():result.end()]
			litstr = litstr.replace(toReplace, token)
			result = m.search(litstr)
		
		finalStr = litstr
		return finalStr
	
	def compileRe(self, reStr):
	    m=re.compile(r'_([^_]+)_')
	    result = m.search(reStr)
	    while result:
			prop = result.group(1)
			orList = self.propsMap[prop]
			orRegex = '(?:'+'|'.join(orList)+')'
			toReplace = reStr[result.start():result.end()]
			reStr = reStr.replace(toReplace, orRegex)
			result = m.search(reStr)

	    finalRegex = reStr
	    return finalRegex

	def toPrimaryTokens(self, literal):
		strIO = StringIO.StringIO(literal)
		scanner = Pyrex.Plex.Scanner(self.lexicon, strIO, "LitScanner")
		tokenList = []
		while True:
			token = scanner.read()
			
			if token[0] == None:
				break
			elif token[0] == '#':
				tokenList.append('#'+token[1])
			else:
				tokenList.append(token[0])
		
		return tokenList

	def tokensToCodes(self, tokens, markerRange=None):
		codeStr = u''
		
		counter = 0
		newStart = 0
		newStop = 0
		
		tokensStr = ''.join(tokens)

		aksharaIter = re.finditer(self.aksharaPattern, tokensStr)
		aksharaList = [akshara.group() for akshara in aksharaIter if len(akshara.group())>0]

		counter = 0
		startMarked = False
		stopMarked = False
		tokenCounter = 0
		for akshara in aksharaList:

			tokens = [akshara[i:i+2] for i in range(0, len(akshara), 2)]
			
			tempStart = counter
			for t in tokens:
				if t[0] != '#':
					codeStr += self.token2code[t]
					counter += len(self.token2code[t])
				else:
					codeStr += t[1]
					counter += len(t[1])
				tokenCounter +=1
			
			if markerRange != None and startMarked == False:
				if tokenCounter >= (markerRange[0]+1):
					newStart = tempStart
					startMarked = True

			if markerRange != None and stopMarked == False:
				if tokenCounter >= markerRange[1]:
					newStop = counter
					stopMarked = True
		
		mRange = None
		if newStop > newStart:
			mRange = (newStart, newStop)
			
		return (codeStr, mRange)
	
	def literalPreProc(self, literal):
		procs = self.preProcs
		for (rule, subst) in procs:
			literal = re.sub(rule, subst, literal)
		
		return literal

	def primaryToUnicode(self, literal, markerRange = None):
		tokenList = self.toPrimaryTokens(literal)

		tokenListFinal = []
		tokenStrFinal = ''
		tokenStr = "".join(tokenList)

		newMarkerRangeBegin = -1
		newMarkerRangeEnd = -1
		
		newMarkerRange = None
		for (index, token) in enumerate(tokenList):
			if token[0] != '#':
				producers = self.renderRules[token]

				bestMatchLen=0
				currRepl = ''
				for (regStr, repl) in producers:
					iter = re.finditer(regStr, tokenStr)
					for match in iter:
						matchLen = len(match.group())
						matchIndex = match.start(1)
						if matchLen > bestMatchLen and matchIndex == 2*index: #each token is guaranteed to be of length 2. so, index in str will be 2*index in list
							currRepl = repl
							bestMatchLen = matchLen			
			else:
				currRepl = token

			if markerRange != None:
				if index == markerRange[0]:
					newMarkerRangeBegin = len(tokenStrFinal)/2
					newMarkerRangeEnd = newMarkerRangeBegin + len(currRepl)/2
				elif index > markerRange[0] and index < markerRange[1]:
					newMarkerRangeEnd += len(currRepl)/2

			tokenStrFinal += currRepl

		tokenListFinal = [tokenStrFinal[i:i+2] for i in range(0, len(tokenStrFinal), 2)]
		
		if newMarkerRangeBegin >= 0 and newMarkerRangeEnd <= len(tokenListFinal):
			newMarkerRange = (newMarkerRangeBegin, newMarkerRangeEnd)

		(codeStr, retMarkerRange) = self.tokensToCodes(tokenListFinal, newMarkerRange)
		
		return (codeStr, retMarkerRange)
	
	def checkProp(self, token, prop):
		if token in self.propsMap[prop]:
			return True
		return False
	
	def unicodeToPrimaryOld(self, uStr):
		tokenList = []
		for uChar in uStr:
			try:
				tokenList.append(self.code2token[uChar])
			except KeyError:
				tokenList.append('#'+uChar)
		
		prevIsCons = False
		
		tokenListInternal = []
		for (i, tk) in enumerate(tokenList):
			if prevIsCons == True and self.checkProp(tk, 'nukta'):
				tokenListInternal.append(tk)
				continue
			if prevIsCons == True:
				if self.checkProp(tk, 'cons'):
					tokenListInternal.append(self.lit2token['a0'])
					tokenListInternal.append(tk)
				elif self.checkProp(tk, 'vowel'):
					tokenListInternal.append(self.lit2token['a0'])
					tokenListInternal.append(tk)
					prevIsCons = False
				elif self.checkProp(tk, 'dot'):
					if i == len(tokenList)-1 or self.checkProp(tokenList[i+1], 'cons') == True:
						tokenListInternal.append(self.lit2token['a0'])
						prevIsCons = False
					tokenListInternal.append(tk)
				elif self.checkProp(tk, 'halanth') and i<(len(tokenList)-1):
					if self.checkProp(tokenList[i+1], 'cons') == False:
						tokenListInternal.append(tk)
					prevIsCons = False
				else:
					tokenListInternal.append(tk)
					prevIsCons = False
			else:
				if self.checkProp(tk, 'cons'):
					tokenListInternal.append(tk)
					prevIsCons = True
				else:		
					tokenListInternal.append(tk)
		
		if prevIsCons == True and len(uStr)==1:
			tokenListInternal.append(self.lit2token['a0']) 
		
		
		literal = ''
		for tk in tokenListInternal:
			if tk[0] != '#':
				literal += self.token2lit[tk]
			else:
				literal += tk[1]
		
		literal = ''.join([x for x in literal if x != '0'])
		
		return literal

	def unicodeToPrimary(self, uStr):
		tokenList = []
		for uChar in uStr:
			try:
				tokenList.append(self.code2token[uChar])
			except KeyError:
				tokenList.append('#'+uChar)
		
		tokenStr = ''.join(tokenList)
		tokenStrInternal = ''
		for (index, token) in enumerate(tokenList):
			if token[0] != '#':
				producers = self.utolitRules[token]

				bestMatchLen=0
				currRepl = ''
				for (regStr, repl) in producers:
					iter = re.finditer(regStr, tokenStr)
					for match in iter:
						matchLen = len(match.group())#group with no arguments will return the entire matched string
						matchIndex = match.start(1)
						#if matchLen >= bestMatchLen and matchIndex == index:
						if matchLen > bestMatchLen and matchIndex == 2*index: #each token is guaranteed to be of length 2. so, index in str will be 2*index in list
							currRepl = repl
							bestMatchLen = matchLen
							
			else:
				currRepl = token

			tokenStrInternal += currRepl

		epsilon = self.lit2token['EPS']
		tokenListInternal = [tokenStrInternal[i:i+2] for i in range(0, len(tokenStrInternal), 2) if tokenStrInternal[i:i+2] != epsilon]

		literal = ''
		for tk in tokenListInternal:
			if tk[0] != '#':
				literal += self.token2lit[tk]
			else:
				literal += tk[1]
		
		literal = ''.join([x for x in literal if x != '0'])
		
		return literal

	def unicodeToHelperPair(self, uStr):
		primary = self.unicodeToPrimary(uStr)
		uStrNew = self.primaryToUnicode(primary, None)[0]
		helper = self.unicodeToHelperStr(uStrNew)

		return (helper, uStrNew)
	
	def unicodeToHelperStr(self, uStr):
		primaryStr = self.unicodeToPrimary(uStr)
		strIO = StringIO.StringIO(primaryStr)
		scanner = Pyrex.Plex.Scanner(self.lexicon, strIO, "LitScanner")
		tokenList = []
		while True:
			token = scanner.read()
			if token[0] == None:
				break
			else:
				tokenList.append(token[1])
		
		helperStr = ''
		for token in tokenList:
			try:
				helperStr += self.primary2helper[token]
			except KeyError:
				helperStr += token

		return helperStr		

	def getInsertCorrections(self, currHelper, currUstr, pos, delta):
		(helperTokens, primaryTokens) = self.getTokenListPair(currHelper, currUstr)
		if (len(helperTokens) != len(primaryTokens)) or (pos < 0 or pos > len(currHelper)):
			return ((currHelper, None), [(currUstr, None)])

		leftSlice = currHelper[0:pos]
		midSlice = delta
		rightSlice = currHelper[pos:]

		newHelper = leftSlice+midSlice+rightSlice
		newHelperTokens = self.toHelperTokens(newHelper)
		
		outListLeft = []
		newStart = 0
		oldTokensRetained = 0
		parseLen = 0
		if pos > 0 and oldTokensRetained < len(primaryTokens):
			index = 0
			while parseLen < pos and (helperTokens[index][0]==newHelperTokens[index][0]):
				outListLeft.append([primaryTokens[index][0]])
				oldTokensRetained += 1
				parseLen += helperTokens[index][1]
				index += 1

			newStart = index
		
		litStart = parseLen
		
		outListRight = []
		newStop = len(newHelperTokens)
		parseLen = 0
		if pos < len(currHelper) and oldTokensRetained < len(primaryTokens):
			oldIndex = len(primaryTokens) - 1
			newIndex = len(newHelperTokens) - 1
			while parseLen < (len(currHelper)-pos) and (helperTokens[oldIndex][0]==newHelperTokens[newIndex][0]):
				outListRight.append([primaryTokens[oldIndex][0]])
				oldTokensRetained += 1
				parseLen += helperTokens[oldIndex][1]
				oldIndex -= 1
				newIndex -= 1
			newStop = newIndex + 1

		outListRight.reverse()
		
		litStop = len(newHelper)-parseLen

		outListMiddle = []
		for i in range(newStart, newStop):
			try:
				options = self.helperRules[newHelperTokens[i][0]][1]
			except KeyError:
				options = [newHelperTokens[i][0]]
			outListMiddle.append(options)

		outList = []
		
		outList.extend(outListLeft)
		outList.extend(outListMiddle)
		outList.extend(outListRight)
			
		tokenStart = newStart
		tokenStop = newStop
		
		uLitList = [([], (tokenStart, tokenStop))]
		count = 1
		for (i, options) in enumerate(outList):
			count = count*len(options)
			newList=[]
			for eachOption in options:
				temp = copy.deepcopy(uLitList)
				for x in temp:
					x[0].append(eachOption)
				newList.extend(temp)
			uLitList = newList

		uStrList = []
		for litList in uLitList:
			iLit = ''.join(litList[0])
			uStrList.append(self.primaryToUnicode(iLit, litList[1]))
			
		markerRange = None
		if litStop > litStart:
			markerRange = (litStart, litStop)

		return ((newHelper, markerRange), uStrList)
			
	def getDeleteCorrections(self, currHelper, currUstr, pos, delLen):
		(helperTokens, primaryTokens) = self.getTokenListPair(currHelper, currUstr)
		
		if (len(helperTokens) != len(primaryTokens)) or (pos < 0 or pos >= len(currHelper)):
			return ((currHelper, None), [(currUstr, None)])

		newHelper = list(currHelper)
		del newHelper[pos:pos+delLen]
		newHelper = ''.join(newHelper)

		newHelperTokens = self.toHelperTokens(newHelper)

		outListLeft = []
		newStart = 0
		oldTokensRetained = 0
		parseLen = 0
		if pos > 0 and oldTokensRetained < len(primaryTokens):
			index = 0
			while (parseLen < pos) and (helperTokens[index][0]==newHelperTokens[index][0]):
				outListLeft.append([primaryTokens[index][0]])
				oldTokensRetained += 1
				parseLen += helperTokens[index][1]
				index += 1
			newStart = index

		litStart = parseLen
		
		outListRight = []
		parseLen =0
		newStop = len(newHelperTokens)
		if (pos+delLen) < len(currHelper) and oldTokensRetained < len(primaryTokens):
			oldIndex = len(primaryTokens) - 1
			newIndex = len(newHelperTokens) - 1
			while parseLen < (len(currHelper)-pos-delLen) and (helperTokens[oldIndex][0]==newHelperTokens[newIndex][0]):
				outListRight.append([primaryTokens[oldIndex][0]])
				oldTokensRetained += 1
				parseLen += helperTokens[oldIndex][1]
				oldIndex -= 1
				newIndex -= 1
			newStop = newIndex + 1

		outListRight.reverse()
		
		litStop = len(newHelper)-parseLen
		
		outListMiddle = []
		for i in range(newStart, newStop):
			try:
				options = self.helperRules[newHelperTokens[i][0]][1]
			except KeyError:
				options = [newHelperTokens[i][0]]
			outListMiddle.append(options)

		outList = []
		
		outList.extend(outListLeft)
		outList.extend(outListMiddle)
		outList.extend(outListRight)

		tokenStart = newStart
		tokenStop = newStop
		
		uLitList = [([], (tokenStart, tokenStop))]
		count = 1
		for (i, options) in enumerate(outList):
			count = count*len(options)
			newList=[]
			for eachOption in options:
				temp = copy.deepcopy(uLitList)
				for x in temp:
					x[0].append(eachOption)
				newList.extend(temp)
			uLitList = newList

		uStrList = []
		for litList in uLitList:
			iLit = ''.join(litList[0])
			uStrList.append(self.primaryToUnicode(iLit, litList[1]))
			
		markerRange = None
		if litStop > litStart:
			markerRange = (litStart, litStop)

		return ((newHelper, markerRange), uStrList)

	def getOptionsAt(self, currHelper, currUstr, pos):
		(tokenList, currList) = self.getTokenListPair(currHelper, currUstr)
		if len(currList) != len(tokenList):
			return ((currHelper, None), [(currUstr, None)])
		
		pos = max(1, pos)
		pos = min(len(currHelper), pos)
		
		posIndex = self.getTokenListPos(tokenList, pos)

		outList = []

		for (i, tu) in enumerate(currList):
			if i == posIndex:
				try:
					options = self.helperRules[tokenList[i][0]][1]
				except KeyError:
					options = [tokenList[i][0]]
				outList.append(options)
			else:
				outList.append([currList[i][0]])
		
		litStart = 0
		for i in range(posIndex):
			litStart += len(tokenList[i][0])

		litStop = litStart + len(tokenList[posIndex][0]) 

		tokenStart = posIndex
		tokenStop = posIndex + 1
		
		uLitList = [([], (tokenStart, tokenStop))]
		count = 1
		for (i, options) in enumerate(outList):
			count = count*len(options)
			newList=[]
			for eachOption in options:
				temp = copy.deepcopy(uLitList)
				for x in temp:
					x[0].append(eachOption)
				newList.extend(temp)
			uLitList = newList
		
		uStrList = []
		for litList in uLitList:
			iLit = ''.join(litList[0])
			uStrList.append(self.primaryToUnicode(iLit, litList[1]))

		markerRange = None
		if litStop > litStart:
			markerRange = (litStart, litStop)

		return ((currHelper, markerRange), uStrList)
		
	def toHelperTokens(self, currHelper):
		strIO = StringIO.StringIO(currHelper)
		scanner = Pyrex.Plex.Scanner(self.helperLexicon, strIO, "HelperLitScanner")
		
		tokenList = []
		while True:
			token = scanner.read()
			if token[0] == None:
				break
			else:
				tokenList.append((token[0], len(token[0])))

		return tokenList
		
	def getTokenListPair(self, currHelper, currUstr):
		currPrimary = self.unicodeToPrimary(currUstr)
		tokenList = self.toHelperTokens(currHelper)
		
		currList = []
		unparsed = currPrimary

		for (i, token) in enumerate(tokenList):
			try:
				options = self.helperRules[token[0]][1]
			except KeyError:
				options = [token[0]]
				
			lexiconParams = []
			for op in options:
				lexiconParams.append((Pyrex.Plex.Str(op), Pyrex.Plex.TEXT ))
			
			tmpLexicon = Pyrex.Plex.Lexicon(lexiconParams)

			tempIO = StringIO.StringIO(unparsed)
			tmpScanner = Pyrex.Plex.Scanner(tmpLexicon, tempIO, "TmpScanner")
			tkn = tmpScanner.read()
			if tkn == None:
				assert(False)
			charPos = tmpScanner.position()[2]
			if charPos != 0:
				assert(False)

			currList.append((tkn[0], len(tkn[0])))
			unparsed = unparsed[len(tkn[0]):]
			if len(unparsed) == 0 and (i+1) < len(tokenList):
				extn = [(self.helperRules[x][1][0], len(self.helperRules[x][1][0])) for (x, y) in tokenList[i+1:] ]
				currList.extend(extn)
				break
		
		return (tokenList, currList)

	def getTokenListPos(self, tokenList, litPos):
		index = 0
		currPos = 0
		posIndex = -1
		for (key, length) in tokenList:
			currPos += length
			if currPos >= litPos:
				posIndex = index
				break
			else:
				index += 1

		return posIndex
