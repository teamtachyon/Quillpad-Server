# -*- coding: utf-8 -*-
# @Date    : Jan 25, 2013
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

import sys
import math

class CARTWord(object):
    __slots__= ['word', 'focus', 'classID', 'count']

    def __init__(self, w, f, cID=u'\u0000', freq=1):
        self.word = w
        self.focus = f
        self.classID = cID
        self.count = freq
    
    def incCount(self, freq=1):
        self.count += freq
    
    def getCount(self):
        return self.count
    
    def getKey(self, scope):
        start = max(self.focus-scope, 0)
        end = min(self.focus+scope, len(self.word))
        
        trimword = self.word[start:end+1]
        trimfocus = self.focus - start
        
        return trimword+str(trimfocus)
    
    def trimToScope(self, scope):
        start = max(self.focus-scope-1, 0)
        end = min(self.focus+scope+1, len(self.word))
        self.word = self.word[start:end+1]
        self.focus = self.focus - start

class splitRule(object):
    __slots__= ['contextFeature', 'relativeIndex', 'contextId']

    def __init__(self, rel=0, contxtId=-1, contextFeature=None ):
        self.relativeIndex = rel
        self.contextId = contxtId
        self.contextFeature = contextFeature

    def setRule(self, rel, contxtId):
        self.relativeIndex = rel
        self.contextId = contxtId

    def setContextFeature(self, feature):
        self.contextFeature = feature
        self.contextId = -1        

class CART(object):
    __slots__= ['classId', 'wordList', 'leftCART', 'rightCART', 'nodeSplitRule', 'terminal', 
        'contextLen', 'splFeatures', 'treeFocus', 'nodeID', 'features', 'contextPrefOrder']

    def __init__(self, key, cartWords=[], contextLength=4, specialFeatures=[], contextPrefOrder=None):
        self.wordList = cartWords
        self.treeFocus = key
        self.leftCART = None
        self.rightCART = None
        self.nodeSplitRule = splitRule()
        self.contextLen = contextLength
        self.features = specialFeatures[:]
        self.splFeatures = specialFeatures[:]
        self.assignFeatures()
        
        self.contextPrefOrder = []
        if contextPrefOrder == None:
                    
            sign=-1
            sign=1
            for delta in [ (n+1)/2 for n in range(0, 2*self.contextLen+1)]:
                delta = delta*sign
                sign = -sign
                self.contextPrefOrder.extend([delta])
        else:
            self.contextPrefOrder = contextPrefOrder
    
    def setCARTNode(self, key, nodeId, cntxtLen, spltRule, terminalStatus, classes):
        self.treeFocus = key
        self.nodeID = nodeId
        self.contextLen = cntxtLen
        self.nodeSplitRule = spltRule
        self.terminal = terminalStatus
        self.classId = classes

    def assignFeatures(self):
        contextFeatures = {}
        for cWord in self.wordList:
            literal = "#"+cWord.word+"_"
            minIndex = max(0, cWord.focus+1- self.contextLen)
            maxIndex = min(len(literal)-1, cWord.focus+1+self.contextLen)
            for i in range( minIndex, maxIndex+1):
                val = [literal[i]]
                val.append("Is letter "+literal[i]+"?")
                contextFeatures.update({literal[i]:val})
            
        self.features.extend(contextFeatures.values())
        
        tupleFeatures =[]
        for li in self.features :
            tupleFeatures.append( tuple(li) )
        
        self.features = tupleFeatures

    def assignClassID(self):
        maxVal = 0
        wList = self.wordList
        if len(wList) > 0 and self.isTerminal():
            counter = {}
            for cWord in wList:
                cid = cWord.classID
                try:
                    counter[cid] += 1*cWord.count
                except KeyError:
                    counter[cid] = 1*cWord.count

            items = counter.items()
            items.sort(cmp=lambda x, y:cmp(y, x), key=lambda x:x[1])
            self.classId = items
            
    def match(self, cWord, rule):
        word = "#"+cWord.word+"_"
        realIndex = cWord.focus+1+rule.relativeIndex
        if realIndex < 0 or realIndex >= len(word):
            return False
        else:
            if rule.contextId != -1:
                features = self.features[rule.contextId]
            else:
                features = rule.contextFeature
            for f in features:
                if f =='':
                    continue
                stop = min(len(word), realIndex+len(f))
                if f == word[realIndex:stop]:
                    return True
            return False

    def nodeAccuracy(self):
        accuracy = 0.0
        wList = self.wordList

        counter = {}
        totalWords = 0
        for cWord in wList:
            cid = cWord.classID
            totalWords += cWord.count
            try:
                counter[cid] += 1*cWord.count
            except KeyError:
                counter[cid] = 1*cWord.count
        
        accuracy = 1.0*sum(count*count for count in counter.values())/totalWords
        
        return accuracy/totalWords

    def splitAccuracy(self, rule):
        leftCounter={}
        rightCounter={}

        leftAccuracy=0
        rightAccuracy=0

        leftCount = 0;
        rightCount = 0;
        
        wList = self.wordList
        
        ruleMatch = self.match
        for cWord in wList:
            if ruleMatch(cWord, rule):
                leftCount += 1*cWord.count
                if leftCounter.has_key(cWord.classID):
                    leftCounter[cWord.classID] += 1*cWord.count
                else:
                    leftCounter[cWord.classID] = 1*cWord.count
            else:
                rightCount += 1*cWord.count
                if rightCounter.has_key(cWord.classID):
                    rightCounter[cWord.classID] += 1*cWord.count
                else:
                    rightCounter[cWord.classID] = 1*cWord.count

        if( leftCount != 0 ):
            leftAccuracy = 1.0*sum([count*count for count in leftCounter.values()])
            leftAccuracy = leftAccuracy/leftCount
        
        if( rightCount != 0 ):
            rightAccuracy = 1.0*sum([count*count for count in rightCounter.values()])
            rightAccuracy = rightAccuracy/rightCount

        accuracy = (leftAccuracy+rightAccuracy)/(leftCount+rightCount)
        return  accuracy
            
    def bestSplit(self):
        currAccuracy = self.nodeAccuracy()
        
        if currAccuracy == 1:
            return None

        bestAccuracy = currAccuracy

        bestRule = splitRule()
        tempRule = splitRule()
        
        for delta in  self.contextPrefOrder:
            for i in range(0, len(self.features)):
                tempRule.setRule(delta, i)
                newAccuracy = self.splitAccuracy(tempRule)

                if newAccuracy > bestAccuracy :
                    bestAccuracy = newAccuracy
                    bestRule.setRule(tempRule.relativeIndex, tempRule.contextId)
                    
                if bestAccuracy == 1:
                    return bestRule

        if bestAccuracy > currAccuracy:
            return bestRule
        else:
            return None

    def split(self, bestRule):
        self.terminal = False
        self.nodeSplitRule = bestRule 

        leftWords = []
        rightWords = []

        for i in range( 0, len(self.wordList)):
            if self.match(self.wordList[i], bestRule):
                leftWords.extend([self.wordList[i]])
            else:
                rightWords.extend([self.wordList[i]])

        self.leftCART= CART(self.treeFocus, leftWords, self.contextLen, self.splFeatures, self.contextPrefOrder)
        self.rightCART = CART(self.treeFocus, rightWords, self.contextLen, self.splFeatures, self.contextPrefOrder)
        
    def build( self ):
        if len(self.wordList) == 0 :
            return

        bestRule = self.bestSplit()

        if bestRule != None:
            self.split(bestRule)
            self.leftCART.build()
            self.rightCART.build()
            nodeFeature = self.features[self.nodeSplitRule.contextId]
            self.nodeSplitRule.setContextFeature(nodeFeature)
        else:
            self.terminal = True
            self.assignClassID()
            

        del self.wordList
        del self.splFeatures
        del self.features
            
    def isTerminal(self):
        return self.terminal == True
    
    def letterToClassLookup(self, word, focus):
        node = self
        cartWord = CARTWord(word, focus)
        return letterToClassID(cartWord, False)

    def letterToClassID(self, cartWord, multiple=False):
        node = self
        while not node.isTerminal():
            rule = node.nodeSplitRule
            if node.match(cartWord, rule):
                node = node.leftCART
            else:
                node = node.rightCART
        
        retValue = [c for (c, i) in node.classId]

        if multiple == True:
            return retValue
        else:
            return retValue[0]

    def getNodeLabel(self, node):
        if node.isTerminal():
            label = ", ".join(["(%s, %s)"%(x, y) for (x, y) in node.classId])
            terminalInfo = label.encode('utf-8')
            return terminalInfo
        return "At %d\\n%s"%(node.nodeSplitRule.relativeIndex, node.nodeSplitRule.contextFeature[-1])

    def getNodeClassRepr(self, node):
        if node.isTerminal():
            label = ", ".join(['("%s", %s)'%(x.encode('utf-8'), y) for (x, y) in node.classId])
            terminalInfo = "[%s]"%label
            return terminalInfo
        
        return "[]"

    def inOrderSetLabel(self, labelGen, node):
        if node.isTerminal():
            node.nodeID = labelGen.next()
            return
        self.inOrderSetLabel(labelGen, node.leftCART)
        node.nodeID = labelGen.next()
        self.inOrderSetLabel(labelGen, node.rightCART)
    
    def preOrderWrite(self, f, node):
        node.writeToFile(f)
        if node.isTerminal():
            return
        self.preOrderWrite(f, node.leftCART)
        self.preOrderWrite(f, node.rightCART)
    
    def storeCart(self, f, treeType='predictive'):
        f.write('\t<tree key="%s" type="%s">\n'%(self.treeFocus, treeType))
        def labelGen():
            i=0
            while 1:
                i=i+1
                yield i
        lblGen = labelGen()
        self.inOrderSetLabel(lblGen, self)
        self.preOrderWrite(f, self)
        f.write('\t</tree>\n')
        
    def writeToFile(self, f):
        f.write('\t\t<node id="%d">\n'%self.nodeID)
        relIndex = self.nodeSplitRule.relativeIndex
        f.write('\t\t\t<split-rule>\n')
        f.write('\t\t\t\t<rel-index>%d</rel-index>\n'%relIndex)
        contextId = self.nodeSplitRule.contextId
        f.write('\t\t\t\t<context-id>%s</context-id>\n'%contextId)
        contextFeature = repr(self.nodeSplitRule.contextFeature)
        f.write('\t\t\t\t<feature>%s</feature>\n'%contextFeature)
        f.write('\t\t\t</split-rule>\n')
        cLen = self.contextLen
        f.write('\t\t\t<context-len>%s</context-len>\n'%cLen)
        terminalStatus = self.isTerminal()
        f.write('\t\t\t<terminal>%s</terminal>\n'%terminalStatus)
        
        classAssigns = self.getNodeClassRepr(self)
        f.write('\t\t\t<classes>%s</classes>\n'%classAssigns)
        f.write('\t\t</node>\n')
        

    def addBinaryNode(self, node):
      cart = self
      while True:     
          if(node.nodeID < cart.nodeID):
              if cart.leftCART is None:
                  cart.leftCART = node
                  return
              cart = cart.leftCART
          else:
              if cart.rightCART is None:
                  cart.rightCART = node
                  return
              cart = cart.rightCART
    
    @staticmethod
    def prepareTrainingData(li, scope, freq):
        data = {}
        for trainingPair in li:
            (literal, classes) = trainingPair
            i=0
            for c in literal:
                cMap={}
                if data.has_key(c):
                    cMap = data[c]
                else:
                    data[c] = cMap

                word = "".join(literal)
                cWord = CARTWord(word, i, classes[i], freq)

                if cMap.has_key(cWord.getKey(scope)) == False:
                    cMap[cWord.getKey(scope)] = cWord
                i+=1
                              
        finalData = {}
        for (k, v) in data.items():
            finalData[k]=v.values()

        return finalData
        

if __name__ == "__main__":
    words =[CARTWord("topi", 0, u'\u0c9f')]
    words.extend([CARTWord("pata", 2, u'\u0c9f')])
    words.extend([CARTWord("tande", 0, u'\u0ca4')])
    words.extend([CARTWord("hosatu", 4, u'\u0ca4')])
    words.extend([CARTWord("hosatana", 4, u'\u0ca4')])
    words.extend([CARTWord("vasati", 4, u'\u0ca4')])
    words.extend([CARTWord("vasanta", 5, u'\u0ca4')])
    words.extend([CARTWord("tagaru", 0, u'\u0c9f')])
    words.extend([CARTWord("takadi", 0, u'\u0ca4')])
    words.extend([CARTWord("vata", 2, u'\u0c9f')])
    words.extend([CARTWord("rata", 2, u'\u0ca4')])
    words.extend([CARTWord("virata", 4, u'\u0c9f')])
    words.extend([CARTWord("viratanagara", 4, u'\u0c9f')])
    words.extend([CARTWord("rajavirata", 8, u'\u0c9f')])
    words.extend([CARTWord("rati", 2, u'\u0ca4')])
    
    vowels = ['a', 'e', 'i', 'o', 'u', 'y', "Is letter a vowel ?"]
    cons1 = ['k', 'K', 'g', 'G', 'c', 'C', 'j', 'J', 't', 'T', 'd', 'D', 'n', '', "Is letter a G1 Cons ?"]        
    cons2 = ['p', 'f', 'b', 'B', 'm', "Is letter a G2 Cons ?"]        
    cons3 = ['y', 'r', 'l', 'v', 'w', 'S', 's', 'h', "Is letter a G3 Cons ?"]        
    
    cons =[]
    cons.extend(cons1[0:-1])
    cons.extend(cons2[0:-1])        
    cons.extend(cons3[0:-1])
    cons.append('Is letter a Cons ?')
    
    splRules = []
    
    splRules.append(vowels)
    splRules.append(cons1)
    splRules.append(cons2)
    splRules.append(cons3)
    splRules.append(cons)

    myCart = CART('t', words, 4, splRules)
    myCart.build()
    
    for word in words:
        print (myCart.letterToClassID(word)).encode('utf-8')

    word = CARTWord("soti", 2, u'\u0ca4')
    print (myCart.letterToClassID(word)).encode('utf-8')
