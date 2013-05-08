import sys, os, random, thread
from PyQt4 import QtGui, QtCore

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

progname = os.path.basename(sys.argv[0])
progversion = "0.1"


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.sub_figure = fig.add_subplot(111)

        
        # We want the axes cleared every time plot() is called
        self.sub_figure.hold(False)

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class StaticCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""
    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.sub_figure.plot(t, s)
        self.sub_figure.axis([-10,10,-10,10])
        #self.title("poo")
        #self.pylab.axis([-10,10,-10,10])


class DynamicCanvas(MyMplCanvas):
    
    data = [1,5,10,5]
    
    """A canvas that updates itself every second with a new plot."""
    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), self.update_figure)
        timer.start(.001)
        
        #thread.start_new_thread(self.change_data, ())
        

    def compute_initial_figure(self):
         self.sub_figure.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [ random.randint(0, 10) for i in xrange(4) ]
        
        self.sub_figure.plot(range(len(self.data)), self.data, 'r')
        #self.sub_figure.axis([-10,len(self.data),-10,10])
        self.draw()
        
    def change_data(self):
        
        for i in range(50000):
            self.data.append(i*random.randint(0,5))

# Application window (of the type QMainWindow)
class ApplicationWindow(QtGui.QMainWindow):
    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")
            
        # Make main widget
        self.main_widget = QtGui.QWidget(self)

        # Init. the layout
        layout = QtGui.QVBoxLayout(self.main_widget)
        
        # Init graph widgets
        #top_graph = StaticCanvas(self.main_widget, width=5, height=4, dpi=100)
        bottom_graph = DynamicCanvas(self.main_widget, width=5, height=4, dpi=100)
        
        # Add widgets to layout
        #layout.addWidget(top_graph)
        layout.addWidget(bottom_graph)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.statusBar().showMessage("Wooo python!", 2000)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()


# Initializes the GUI
if __name__== "__main__":
    app = QtGui.QApplication(sys.argv)
    
    gui = ApplicationWindow()
    gui.setWindowTitle("%s" % progname)
    gui.show()
    
    sys.exit(app.exec_())