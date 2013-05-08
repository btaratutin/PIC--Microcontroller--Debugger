"""
Boris Taratutin
Sat Apr 24 22:53:18 2010


"""

import time
from pylab import *
#import pylab
import sys
import random
import thread


def poo():
    print "poo"

class ContinualPlot:
    
    data = []
    plot_data = []
    curr_axis_length = 10
    X_AXIS_INCREMENT = 10
    Y_AXIS_INCREMENT = 10
    MAX_SAMPLES_WINDOW = 200            # How many samples fit into a window before we begin scrolling
    
    def __init__(self):
        ion()                                               # Allows continual update plotting
        self.myfig = figure(1)                              # Create Figure
        self.mysubplot = subplot(111)                       # Create Subplot
        self.myplot = plot(0, 0)                            # Plot first point
        axis([0, 10, 0, 3])                                # Set default axes
        xlabel('Data sample #')
        ylabel('voltage (V)')
        title('Continual Output')
        grid(True)
        draw()
        
    
    # Updates axes if necessary
    def updateAxes(self, new_val):
        # Update X-axis
        if (len(self.plot_data) < self.MAX_SAMPLES_WINDOW):                     # For scrolling
            if (len(self.data) >= self.curr_axis_length):
                self.curr_axis_length += self.X_AXIS_INCREMENT
                self.mysubplot.set_xlim(0, self.curr_axis_length) # Sets the x-axis labels
        
        """
        # If new value is below the y min. range, update it
        if (new_val < self.mysubplot.get_ylim()[0]):
           self.mysubplot.set_ylim(ymin = new_val-self.Y_AXIS_INCREMENT )
           
        # Do the same with the max
        if (new_val > self.mysubplot.get_ylim()[1]):
            self.mysubplot.set_ylim(ymax = new_val+self.Y_AXIS_INCREMENT )
        """


    # Call to update data that is being plotted
    def addData(self, new_val):
        self.data.append(new_val)                                               # Sets data to new one
        
        # (for scrolling) If the plot window has filled up, pop the first val before appending
        if (len(self.plot_data) >= self.MAX_SAMPLES_WINDOW):
            self.plot_data.pop(0)
        self.plot_data.append(new_val)
        # plot either from 0 or the last # MAX_SAMPLES_WINDOW vals
        self.myplot[0].set_data(range(max(0, len(self.plot_data) - self.MAX_SAMPLES_WINDOW), len(self.plot_data)), self.plot_data)               # Updates the actual plot with the new data
        self.updateAxes(new_val)                                                # Checks whether the axes need changing
        draw()                                                                  # Redraws figure
        
    def exit(self):
        pass
        
# Test loop
def myDataLoop(*args):
    
    print args
    plot = args[1]
    
    while(1):
        new_val = random.randint(0,100)
        plot.addData(new_val)
        time.sleep(.1)

    

if __name__=="__main__":
    print "Starting program"
    plot = ContinualPlot()
    
    thread.start_new_thread(myDataLoop, (0, plot) )
    
    print "press enter to exit"
    raw_input()
    plot.close()
    sys.exit(app.exec_())

