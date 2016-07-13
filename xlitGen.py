import sys
import QuillEngXlit

def main() :
    if len(sys.argv) < 4 :
        print "Usage : xlitGen.py <inputFile> <outputTrainingFile> <outputMappingFile>"
        return
    xlitEngine = QuillEngXlit.QuillEngXliterator('EnglishPronouncingTrees','IndianPronouncingTrees','Kannada_Xlit.xml')
    lines = open(sys.argv[1],'rb').readlines()
    xlits = {}
    xlitMapping = {}
    for line in lines :
        (word,freq) = line.strip().split()
        xlitWords = xlitEngine.xliterate(word)
        if len(xlitWords) == 0 :
            continue
        if xlitWords[0] not in xlits :
            xlits[xlitWords[0]] = 0
        xlits[xlitWords[0]] = xlits[xlitWords[0]] + int(freq)
        if xlitWords[0] not in xlitMapping :
            xlitMapping[xlitWords[0]] = []
        xlitMapping[xlitWords[0]].append( word )

    o1 = open(sys.argv[2],'wb')
    for (xlit,freq) in xlits.items() :
        o1.write( xlit.encode('utf-8') + '\t' + str(freq) + '\r\n' )
    o1.close()

    o2 = open(sys.argv[3],'wb')
    for (xlit,words) in xlitMapping.items() :
        o2.write( xlit.encode('utf-8') + '\t' + '\t'.join(words) + '\r\n' )
    o2.close()

if __name__ == '__main__':
    main()
