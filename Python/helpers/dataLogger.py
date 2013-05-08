"""
Boris Taratutin
01.12.2010

Data Logger Module - makes writing to files easy
"""

import os
import datetime

def bin8(val):                  # ensures binary return value has leading 0's (total of 8)
    newval = bin(val)           # bin() adds 0b... therefore goal length is 10
    while (len(newval) < 10):
        newval = newval[0:2] + '0' + newval[2:]
        
    return newval


def makeDir():                  # If 'data' directory does not exist, create it
    dir_name = "%s\\data" % os.getcwd()
    if not os.path.exists(dir_name):    #if directory does not exist
        os.makedirs(dir_name)           # make it
        
        
def format_output(s):           # Converts passed in list to formatted output string
    # Convert all values to strings
    s = [str(val) for val in s]
    
    # Create formatted string
    sout = ''
    for i in range(len(s)):
        val = s[i]
        if (i < 6):             # Convert port & tris vals to binary
            val = bin8(int(val))
            sout += val.ljust(15)
        else:                   # Append the rest of the values
            sout += val.ljust(8)
            
    # Add timestamp
    now = datetime.datetime.now()
    now_s = "%d:%d:%d:%s" % (now.hour, now.minute, now.second, str(now.microsecond)[0:2])
    
    sout += now_s.ljust(20)
        
    
    return sout
    
def makeHeaders():             # Writes the headers for the file
    headers = ( "{0}{1}{2}{3}{4}{5}{6}{7}{8}{9}{10}{11}{12}{13}{14}".format(
    "PORTA".ljust(15), "PORTB".ljust(15), "PORTC".ljust(15),
    "TRISA".ljust(15), "TRISB".ljust(15), "TRISC".ljust(15),
    "dm0".ljust(8), "dm1".ljust(8), "dm2".ljust(8),
    "dm8".ljust(8), "dm4".ljust(8), "dm5".ljust(8),
    "dm6".ljust(8), "dm7".ljust(8), "timestamp".ljust(20) ) )
    headers += "\n\n"
    
    return headers

