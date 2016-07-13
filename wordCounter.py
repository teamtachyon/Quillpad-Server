from flask import Flask, request, render_template, redirect, url_for
import itertools, threading, json
import time

from RingBuffers import RingBuffer, RingBufferFull

app = Flask(__name__)

lock = threading.Lock()
prevTime = time.time()
wordCount = itertools.count(int(open('wordcount').read()))
timerRingBuffer = RingBuffer(10, wordCount.next())
    
@app.route("/processInput")
def processInput():
    action = request.args.get('action')
    if action <> 'addWord':
        return
    count = wordCount.next()
    
    if count % 100 == 0:
        updateCount(count)
    #print 'wordcount is: ', wordCount
    
    currTime = int(time.time())
    global prevTime
    global timerRingBuffer
    if currTime <> prevTime:
        timerRingBuffer.append(wordCount)
        prevTime = currTime
    else:
        timerRingBuffer.data[timerRingBuffer.get_curr()] = count
        
    return ""
    #print 'buffer is: ', timerRingBuffer.get()

@app.route("/processWordCounts")
def processWordCounts():
    print 'buffer is: ', timerRingBuffer.get()
    print 'response is', json.listToJSON(timerRingBuffer.get())
    print
    return json.listToJSON(timerRingBuffer.get())
    
def updateCount(count):
    lock.acquire()
    open('wordcount', 'w').write(str(count))
    lock.release()
    
    
if __name__ == "__main__":
    app.run(debug=True)
