# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 19:04:01 2010

@author: btaratutin
"""
import thread
import numpy
import pylab

data = [1, 5, 7]



def liveLogInit():
    print "initiating live data log"
        
    
    
    #thread.start_new_thread(liveDataLog, ())
    
    pylab.plot(range(len(data)), data)
    pylab.xlabel('time (s)')
    pylab.ylabel('voltage (V)')
    pylab.title('About as simple as it gets, folks')
    pylab.grid(True)
    pylab.savefig('simple_plot')
    pylab.show()
    
    #pylab.clf()
    pylab.plot([1,2,3], [10,15,5])
    pylab.show()
    
    
    
    

def liveDataLog():
    print "starting live data log"
    
    for i in range(50000):
        print i
        
    print "\n\n done!"
    
    """
    pylab.show()

    #pylab.show()
    
    for i in range(50):
        data.append(i)
        pylab.clf()
        pylab.plot(range(len(data)), data)
        pylab.show()
    """
    
    


# Initializes the GUI
if __name__== "__main__":
    liveLogInit()
    
    print"\n\n done. press enter to exit"
    raw_input()
    
