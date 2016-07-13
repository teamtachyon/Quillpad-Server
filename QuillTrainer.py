# -*- coding: utf-8 -*-
# @Date    : Jul 13, 2016
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

import CART
from QuillLanguage import QuillLanguage
import pickle

class QuillTrainer(object):
    def __init__(self,quillLang):
        if isinstance(quillLang,QuillLanguage):
            self.language = quillLang
        else:
            raise Exception,'Invalid parameter. Not of type QuillLanguage' 
    
    def train(self,uWords,scope=4,splRulesFlag=True):
        self.language.setKnowledge(self.__buildKeyToCARTMap(uWords,scope,splRulesFlag,"primary"),"primary")
        self.language.setKnowledge(self.__buildKeyToCARTMap(uWords,scope,splRulesFlag,"predictive"),"predictive")
        return self.language
    
    def getLanguage(self):
        return self.language
    
    def store(self,fname=None):
        if fname == None:
            fname = self.language.language+'.qil'
        
        keyToCARTMap = self.language.keyToCARTMap
        keyToCARTMapPrimary = self.language.keyToCARTMapPrimary
        f = file(fname,'w')
        f.write('<QuillLanguage lang="%s" script="%s" deffont="%s" epsilon="%s">\n'%(self.language.language,self.language.script,self.language.default_font,self.language.epsilon.encode('utf-8')))
        for (key,keyCart) in keyToCARTMap.items():
            keyCart.storeCart(f,"predictive")
        for (key,keyCart) in keyToCARTMapPrimary.items():
            keyCart.storeCart(f,"primary")

        f.write('</QuillLanguage>')
        
        f.close()
    
    def load(self, trainedData):
        pass
        
    def __buildKeyToCARTMap ( self, uWords,scope=4,splRulesFlag=True,type="predictive" ):
        contextLen = scope
        splRules = []
        if splRulesFlag == True:
            splRules = self.language.getSpecialRules(type)

        keyToCARTMap = {}
        data={}
        for uWord in uWords:
            try:
                trainPairs = self.language.getTrainingPairs(uWord,type)
            except KeyError:
                trainPairs = None

            if trainPairs != None:
                data1 = CART.CART.prepareTrainingData(trainPairs,contextLen,1)
    
                for key in data1.keys():
                    if data.has_key(key):
                        data[key].extend( data1[key] )
                    else:
                        data.update({key:data1[key]})

        if type == "primary":
            contextPrefOrder = [0,1,2,-1,3,-2,4,-3-4]
        elif type == "predictive":
            contextPrefOrder = None
            
        for key in data.keys():
            keyCart = CART.CART(key,data[key],contextLen, splRules,contextPrefOrder)
            keyCart.build()
            keyToCARTMap.update( {key:keyCart } )
        
        return keyToCARTMap    

    def createTrainingData( self, uWords,scope=4,splRulesType='predictive',fname = None ):
        contextLen = scope
        
        splRules = []
        if splRulesType != None:
            splRules = self.language.getSpecialRules(splRulesType)

        if fname == None:
            fname = self.language.language+'.data'
        
        f = file(fname,'w')

        f.write('<QuillTrainData lang="%s" script="%s" deffont="%s" epsilon="%s" context-len="%s">\n'%(self.language.language,self.language.script,self.language.default_font,self.language.epsilon.encode('utf-8'),scope))
        
        f.write('\t<SpecialRules>\n')
        for eachRule in splRules:
            f.write('\t\t<SpecialRule>')
            f.write(repr(eachRule))
            f.write('</SpecialRule>')
            f.write('\n')
        f.write('\t\t</SpecialRules>\n')
        
        keyToCARTMap = {}
        data={}
        for uWord in uWords:
            try:
                trainPairs = self.language.getTrainingPairs(uWord)
            except KeyError:
                trainPairs = None
                
            if trainPairs != None:
                data1 = CART.CART.prepareTrainingData(trainPairs,contextLen,1)
    
                for key in data1.keys():
                    if data.has_key(key):
                        data[key].extend( data1[key] )
                    else:
                        data.update({key:data1[key]})

        for key in data.keys(): 
            keyData = data[key];
            f.write('\t<QuillWordList key="%s">\n'%key)
            for cWord in keyData:
                f.write('\t\t<QuillWord>\n')
                f.write('\t\t\t<Literal>%s</Literal>\n'%cWord.word)
                f.write('\t\t\t<Focus>%s</Focus>\n'%cWord.focus)
                f.write('\t\t\t<ClassAssign>%s</ClassAssign>\n'%cWord.classID.encode('utf-8'))
                f.write('\t\t\t<Count>%s</Count>\n'%cWord.count)
                f.write('\t\t</QuillWord>\n')
            f.write('\t</QuillWordList>\n')
        f.write('</QuillTrainData>\n')            
        f.close()
