#!/usr/bin/python

# System Imports
import sys
import os
import datetime
import ctypes                   # for usb
import time                     # for timing & sleeping
import thread
from PyQt4 import QtGui, QtCore

# My Imports
sys.path.append(".\helpers")
import dataLogger
import Continual_Plot
import ConversionFunctions


# This GUI is written in PyQt. It is awesome. To learn more, check out the following: (it's easy to pick up)
# http://www.learningpython.com/2008/09/20/an-introduction-to-pyqt/
# http://zetcode.com/tutorials/pyqt4/


# USB-PIC Protocol; how they communicate (arbitrary numbers ("vendor requests") set by us)
GET_LED         = 3     # Pic --> USB
SET_LED         = 4     # USB --> Pic

GET_DEBUG_MSG   = 10    # Pic --> USB (can get up to 8 messages)
GET_REGISTERS   = 11    # Pic --> USB (Gets PORT and TRIS Registers)
GET_EEPROM      = 12    # Pic --> USB (gets 256 eeprom bytes)

SET_USB_MSG1    = 20    # USB --> Pic (can send any one message)
SET_USB_MSG2    = 21

SET_PORTA       = 30    # USB --> Pic
SET_PORTB       = 31
SET_PORTC       = 32

SET_TRISA       = 35    # USB --> Pic
SET_TRISB       = 36
SET_TRISC       = 37



class GuiInit(QtGui.QMainWindow):

    # =====      'Global' Variables. Can be accessed anywhere within the class/program      ===== #
       
    # PIC Variables (reflect state of PIC)
    PORTA = 0                       # Status of PIC's PORT registers
    PORTB = 0
    PORTC = 0
    
    TRISA = 0                       # Status of PIC's TRIS registers
    TRISB = 0
    TRISC = 0
    
    debug_message   = range(8)      # The debug message (up to 8 bytes) that the pic sends
    eeprom          = range(256)    # The PIC's eeprom
    led_status = 0                  # PC's thought on what the status of the debug_led is
    
    # Program variables
    live_monitoring = 1             # 1/0. Whether live_monitoring of the system is enabled
    data_logging    = False         # T/F. Whether data is being written to log
    refresh_rate = 20               # Live monitoring frequency (# checks/second) (currently, max ~= 66.6)
    
    
    

    # Initializes the program
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)    # Inits the base class. any call to "self." accesses it
        
        # Self-explanatory
        self.init_usb()                             
        self.create_widgets()
        self.init_window_components()
        self.update_gui()
        thread.start_new_thread(self.main_loop, ())
        

        
        
    # Initializes window title, menu, status bar
    def init_window_components(self):
        
        # Customize look & feel
        self.setWindowTitle("Python PIC Debugger")  # Set the window title
        
        # Initialize and set the status bar
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Ready to rock")


        #           ===== Menu Components =====            #
        exit = QtGui.QAction(QtGui.QIcon('icons/exit.png'), 'Exit', self)
        exit.setShortcut('Ctrl+Q')
        exit.setStatusTip('Exit application')
        self.connect(exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))
        
        save = QtGui.QAction(QtGui.QIcon('icons/save.png'), 'Save PIC State', self)
        save.setShortcut('Ctrl+S')
        save.setStatusTip('Write PIC state to file')
        self.connect(save, QtCore.SIGNAL('triggered()'), lambda : self.log_data(1))
        
        log_data = QtGui.QAction(QtGui.QIcon('icons/data.png'), 'Log Data', self)
        log_data.setShortcut('Ctrl+L')
        log_data.setStatusTip('Start/Stop data logging')
        self.connect(log_data, QtCore.SIGNAL('triggered()'), lambda : self.log_data(999))
        
        eeprom_get = QtGui.QAction(QtGui.QIcon('icons/eeprom.png'), 'Log EEPROM', self)
        eeprom_get.setShortcut('Ctrl+E')
        eeprom_get.setStatusTip('Get & save the EEPROM state')
        self.connect(eeprom_get, QtCore.SIGNAL('triggered()'), self.get_eeprom_clicked)
        
        reset_usb = QtGui.QAction(QtGui.QIcon('icons/usb.png'), 'Reset USB Connection', self)
        reset_usb.setShortcut('Ctrl+R')
        reset_usb.setStatusTip('Reset the USB connection')
        self.connect(reset_usb, QtCore.SIGNAL('triggered()'), self.init_usb)
        
        refresh = QtGui.QAction(QtGui.QIcon('icons/change.png'), 'Change Refresh Rate', self)
        refresh.setStatusTip('Change the rate of data aquisition')
        self.connect(refresh, QtCore.SIGNAL('triggered()'), self.change_refresh_rate)
        
        
        help = QtGui.QAction(QtGui.QIcon('icons/help.png'), 'Help', self)
        help.setShortcut('F1')
        help.setStatusTip('Open the Documentation')
        self.connect(help, QtCore.SIGNAL('triggered()'), self.launch_documentation)
        
        about = QtGui.QAction(QtGui.QIcon('icons/about.png'), 'About', self)
        about.setStatusTip('About this program')
        self.connect(about, QtCore.SIGNAL('triggered()'), lambda :  QtGui.QMessageBox.information(self, "Information for you!", "Created 1.13.2010\nby Boris Taratutin\n\nQuestions, comments, philisophical dilemmas?\nEmail boris.taratutin@gmail.com\n\nRock On.") )
        
        mystery_action = QtGui.QAction('', self)

        # Initialize Menu Bar
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(save)
        file_menu.addAction(log_data)
        file_menu.addAction(eeprom_get)
        file_menu.addAction(reset_usb)
        file_menu.addAction(exit)
        
        edit_menu = menubar.addMenu('&Edit')
        edit_menu.addAction(refresh)
        
        help_menu = menubar.addMenu('&Help')
        help_menu.addAction(help)
        help_menu.addAction(about)
        
        mystery_menu = menubar.addMenu('&Snarglemumplimps')
        mystery_menu.addAction(mystery_action)
        
    
        
        
    # Initializes usb connection (don't worry about this)
    def init_usb(self):
        try:
            self.usb = ctypes.cdll.LoadLibrary('helpers\usb.dll')
            self.usb.initialize()
            
            self.buffer = ctypes.c_buffer(8)
        
            self.dev = self.usb.open_device(0x6666, 0x0003)
            if self.dev<0:
                print "No matching device found...\n"
            else:
                print "OMGLOLZYEY I found a self.usb!\n"
                ret = self.usb.control_transfer(self.dev, 0x00, 0x09, 1, 0, 0, self.buffer)
                if ret<0:
                    print "Unable to send SET_CONFIGURATION standard request.\n"
        except:
            print "unable to load usb dll"




    # Creates the GUI Widgets
    def create_widgets(self):
                                    # ========== Widget Declarations ========== #
        
        # PORT & TRIS Widgets 
        self.PORTA_label = QtGui.QLabel("PORTA: ")          # Note: label text here don't matter. It will be overwritten later
        self.PORTB_label = QtGui.QLabel("PORTB: ")
        self.PORTC_label = QtGui.QLabel("PORTC: ")
        
        self.TRISA_label = QtGui.QLabel("TRISA: ")
        self.TRISB_label = QtGui.QLabel("TRISB: ")
        self.TRISC_label = QtGui.QLabel("TRISC: ")
        
        # PORT Register Actions
        self.PORTA_action = QtGui.QPushButton("set")
        QtCore.QObject.connect(self.PORTA_action, QtCore.SIGNAL('clicked()'), lambda : self.set_register("PORTA"))
        self.PORTB_action = QtGui.QPushButton("set")
        QtCore.QObject.connect(self.PORTB_action, QtCore.SIGNAL('clicked()'), lambda : self.set_register("PORTB"))
        self.PORTC_action = QtGui.QPushButton("set")
        QtCore.QObject.connect(self.PORTC_action, QtCore.SIGNAL('clicked()'), lambda : self.set_register("PORTC"))
        
        # TRIS Register Actions
        self.TRISA_action = QtGui.QPushButton("set")
        QtCore.QObject.connect(self.TRISA_action, QtCore.SIGNAL('clicked()'), lambda : self.set_register("TRISA"))
        self.TRISB_action = QtGui.QPushButton("set")
        QtCore.QObject.connect(self.TRISB_action, QtCore.SIGNAL('clicked()'), lambda : self.set_register("TRISB"))
        self.TRISC_action = QtGui.QPushButton("set")
        QtCore.QObject.connect(self.TRISC_action, QtCore.SIGNAL('clicked()'), lambda : self.set_register("TRISC"))
        
        
        # User Input Widgets
        
        # USB Message 1
        self.usb_msg1_label = QtGui.QLabel("Usb Msg1: ")
        self.usb_msg1_input = QtGui.QLineEdit()
        self.usb_msg1_input.setMaxLength(3)
        self.usb_msg1_action = QtGui.QPushButton("send")
        self.connect(self.usb_msg1_action, QtCore.SIGNAL('clicked()'), self.usb_msg1_clicked)
        
        # USB Message 2
        self.usb_msg2_label = QtGui.QLabel("Usb Msg2: ")
        self.usb_msg2_input = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.usb_msg2_input.setRange(0, 255)
        self.usb_msg2_input.setSingleStep(10)
        self.usb_msg2_input.setValue(127)
        self.usb_msg2_label2 = QtGui.QLabel("(" + str(self.usb_msg2_input.sliderPosition()) + ")") 
        self.connect(self.usb_msg2_input, QtCore.SIGNAL('valueChanged(int)'), self.usb_msg2_clicked)
        
        
        # Debug LED Widget
        self.led_label = QtGui.QLabel("LED: ")
        self.get_led = QtGui.QPushButton("get")
        self.set_led = QtGui.QPushButton("set")
        
        QtCore.QObject.connect(self.get_led, QtCore.SIGNAL('clicked()'), self.get_led_clicked)
        QtCore.QObject.connect(self.set_led, QtCore.SIGNAL('clicked()'), self.set_led_clicked)
            
        
        # Debug Messages Widget
        self.debug_message0_label = QtGui.QLabel("")
        self.debug_message1_label = QtGui.QLabel("")
        self.debug_message2_label = QtGui.QLabel("")
        self.debug_message3_label = QtGui.QLabel("")
        self.debug_message4_label = QtGui.QLabel("")
        self.debug_message5_label = QtGui.QLabel("")
        self.debug_message6_label = QtGui.QLabel("")
        self.debug_message7_label = QtGui.QLabel("")


        
        
                            # ==========      Layout      ========== #
                            
                            
        spacer = QtGui.QSpacerItem(10, 15)
        
                            # ======    GUI LEFT SIDE    ===== #
                            
        # PORT & TRIS Readouts
        
        v_box2 = QtGui.QVBoxLayout()        
        
        # Readout-Set Register Combo
        h_box1 = QtGui.QHBoxLayout()
        h_box1.addWidget(self.PORTA_label)
        h_box1.addWidget(self.PORTA_action)
        v_box2.addLayout(h_box1)
        
        # Readout-Set Register Combo
        h_box1 = QtGui.QHBoxLayout()
        h_box1.addWidget(self.PORTB_label)
        h_box1.addWidget(self.PORTB_action)
        v_box2.addLayout(h_box1)
        
        # Readout-Set Register Combo
        h_box1 = QtGui.QHBoxLayout()
        h_box1.addWidget(self.PORTC_label)
        h_box1.addWidget(self.PORTC_action)
        v_box2.addLayout(h_box1)
        
        
        v_box2.addItem(spacer) # Spacer between PORT & TRIS Registers
        
        
        # Readout-Set Register Combo
        h_box2 = QtGui.QHBoxLayout()
        h_box2.addWidget(self.TRISA_label)
        h_box2.addWidget(self.TRISA_action)
        v_box2.addLayout(h_box2)
        
        # Readout-Set Register Combo
        h_box2 = QtGui.QHBoxLayout()
        h_box2.addWidget(self.TRISB_label)
        h_box2.addWidget(self.TRISB_action)
        v_box2.addLayout(h_box2)
        
        # Readout-Set Register Combo
        h_box2 = QtGui.QHBoxLayout()
        h_box2.addWidget(self.TRISC_label)
        h_box2.addWidget(self.TRISC_action)
        v_box2.addLayout(h_box2)
        

        # User (USB) Message Send Actions
        
        # User Input VBox
        h_box1 = QtGui.QHBoxLayout()
        h_box1.addWidget(self.usb_msg1_label)
        h_box1.addWidget(self.usb_msg1_input)
        h_box1.addWidget(self.usb_msg1_action)
        
        h_box2 = QtGui.QHBoxLayout()
        h_box2.addWidget(self.usb_msg2_label)
        h_box2.addWidget(self.usb_msg2_input)
        h_box2.addWidget(self.usb_msg2_label2)
        
        v_box3 = QtGui.QVBoxLayout()
        v_box3.addLayout(h_box1)
        v_box3.addLayout(h_box2)
        
        
        
                            # ======    GUI RIGHT SIDE    ===== #
        
        # Debug LED HBox
        h_box3 = QtGui.QHBoxLayout()
        h_box3.addWidget(self.led_label)
        h_box3.addWidget(self.get_led)
        h_box3.addWidget(self.set_led)


        # Debug Messages VBox
        v_box4 = QtGui.QVBoxLayout()
        v_box4.addWidget(self.debug_message0_label)
        v_box4.addWidget(self.debug_message1_label)
        v_box4.addWidget(self.debug_message2_label)
        v_box4.addWidget(self.debug_message3_label)
        v_box4.addWidget(self.debug_message4_label)
        v_box4.addWidget(self.debug_message5_label)
        v_box4.addWidget(self.debug_message6_label)
        v_box4.addWidget(self.debug_message7_label)
        
        
        
                            # ======    Combining Everything    ===== #
        
        # RIGHT Vertical Box    (LED + Debug Messages + Start/Stop)
        v_box11 = QtGui.QVBoxLayout()
        v_box11.addLayout(h_box3) # LED get/set
        v_box11.addLayout(v_box4) # Debug Messages
        
        
        # LEFT Vertical Box     (PORT/TRIS Readout/Set + User Messages)
        v_box10 = QtGui.QVBoxLayout()
        v_box10.addLayout(v_box2) # PORT/TRIS
        v_box10.addItem(spacer)
        v_box10.addLayout(v_box3) # User Inputs
        
        
        # Uber HBox
        h_box = QtGui.QHBoxLayout()
        h_box.addLayout(v_box10)
        h_box.addLayout(v_box11)
        
        # Spacing
        h_box.setMargin(10)
        h_box.setSpacing(5)
        v_box10.setMargin(7)
        v_box11.setMargin(7)
        

        
        # Central widget that contains all screen components
        self.central_widget = QtGui.QWidget()
        self.central_widget.setLayout(h_box)
        self.setCentralWidget(self.central_widget)  # Identify the central widget
        
        
        
        
                            # =====      Action Definitions       ===== #
    
    # Prompts the user for a new register value, parses the input, and sends the appropriate command to the PIC
    def set_register(self, register):
        
        # Get User Input
        newval, ok = QtGui.QInputDialog.getText(self, 'Set Register Value', 'Enter new value for %s (in binary): ' % register)
        send = True
        
        # Read the user's response value & convert to binary + error checking
        try:
            newval = int(str(newval), base = 2)
            if (newval < 0  or newval > 255):           # Check for improper values
                newval = 0                              # give default value
            print "%s value read to be %s (%s)" % (register, newval, bin(newval))

        except:
            send = False
            print "ERROR in READING PORTA value. Not sending"
            
        # Send the value (modular method for sending the right values)
        if send:
            try:
                # Hack for a case-switch statement
                dict = { 
                        "PORTA" : lambda: self.usb.control_transfer(self.dev, 0x40, SET_PORTA, newval, 0, 0, self.buffer),
                        "PORTB" : lambda: self.usb.control_transfer(self.dev, 0x40, SET_PORTB, newval, 0, 0, self.buffer),
                        "PORTC" : lambda: self.usb.control_transfer(self.dev, 0x40, SET_PORTC, newval, 0, 0, self.buffer),
                        "TRISA" : lambda: self.usb.control_transfer(self.dev, 0x40, SET_TRISA, newval, 0, 0, self.buffer),
                        "TRISB" : lambda: self.usb.control_transfer(self.dev, 0x40, SET_TRISB, newval, 0, 0, self.buffer),
                        "TRISC" : lambda: self.usb.control_transfer(self.dev, 0x40, SET_TRISC, newval, 0, 0, self.buffer)
                      } #create dictionary that maps each register to the right function
                      
                funcToCall = dict[register]     # select the right function to call, based on register
                funcToCall()                    # call the function to execute the usb statement
                
                print "sent %d" % newval
                self.update_gui()
            except:
                print "ERROR in SENDING %s value" % register
            
    
    
    # User typed in a value and hit 'send' on "usb message 1"
    def usb_msg1_clicked(self):
        
        # Error-check the value, and if it's good, send it
        send = True
        try:
            sendingval = int(str(self.usb_msg1_input.displayText()))
            if (sendingval < 0 or sendingval > 255):
                send = False
                print "Input error. Not sending"
                QtGui.QMessageBox.warning(self,
                            "Warning",
                            "Please enter a value between 0 and 255")
        
        except:
            send = False
            print "Input error. Not sending"
            QtGui.QMessageBox.warning(self,
                            "Warning",
                            """Silly you.. You can't send strings! (yet). 
                            \nPlease enter a number between 0 and 255""")
        
        if send == True:
            self.usb.control_transfer(self.dev, 0x40, SET_USB_MSG1, sendingval, 0, 0, self.buffer)
            print "sent %d" % sendingval
        
        
        
    # User moved the slider titled "usb message 2". Sends slider value
    def usb_msg2_clicked(self, value):
        try:
            self.usb.control_transfer(self.dev, 0x40, SET_USB_MSG2, value, 0, 0, self.buffer)
            print "sent %d" % value
            
        except:
            print "oh no! Something pooped out..."
            
        self.update_gui()
        
        
        
    def get_eeprom_clicked(self):
        print "getting eeprom"
        
        # Asks the pic for the 256 eeprom bytes. Each time, PIC gives next 8 values
        # Thus, we loop 8 bytes * 32 times = 256 total bytes
        for i in range (0, 256/8):
            self.usb.control_transfer(self.dev, 0xC0, GET_EEPROM, 0, 0, 8, self.buffer) #input = #bytes host requesting (the 1)
            for j in range(0, 8):
                index = 8*i + j
                self.eeprom[index] = ord(self.buffer[j]) #ord converts self.buffer characters to ints
                
        print "\nEEPROM is 256 bytes"
        print self.eeprom
        # Write EEPROM to text file
        
        # Figure out time
        now = datetime.datetime.now()
        now_s = "%d.%d.%d - %dh.%dm.%ds" % (now.month, now.day, now.year, now.hour, now.minute, now.second)
        
        # Name file
        filename = "%s\\data\\eeprom - %s - eeprom get.txt" % (os.getcwd(), now_s)
        
        # Make output directory (unless already exists)
        dataLogger.makeDir()
        
        # Open File
        print "Writing to file: %s" % filename
        fout = open(filename, 'w')
        
        # Create output string
        s_out = ""
        for i in range(0, 256):
            s_out += "Byte %d: \t%d\n" % (i, self.eeprom[i])
        
        # Write starting data/time
        fout.write("Eeprom state at: %s\n\n\n" % now_s)
        fout.write(s_out)
        fout.close()
        
        
            
    

    # Simple 'set' command. Inverts the LED's current status and sends it to PIC
    def set_led_clicked(self): 
        self.led_status = inverse(self.led_status)          # Invert LED
        self.usb.control_transfer(self.dev, 0x40, SET_LED, self.led_status, 0, 0, self.buffer) #change led value
        
        self.update_gui()
        print "Set LED to %d" % self.led_status

    # Simple 'get' command. Asks for the value of LED
    def get_led_clicked(self): 
        self.usb.control_transfer(self.dev, 0xC0, GET_LED, 0, 0, 1, self.buffer)
        self.led_status = ord(self.buffer[0])
        
        self.update_gui()
    
    
    
    # Gets the entire 'status' of the PIC (all of it's PORT and TRIS registers, as well as debug messages, etc.).
    # Continually called by threaded loop.
    def get_pic_status(self):
        
        # Get the "Debug Message" (8 bytes of information)
        self.usb.control_transfer(self.dev, 0xC0, GET_DEBUG_MSG, 0, 0, 8, self.buffer) #input = #bytes host requesting (the 1)
   
        # Cycles through the 8 received bytes, and sticks them int othe debug_message, to be printed out later
        for i in range(0, 8):
            self.debug_message[i] = ord(self.buffer[i]) #ord converts self.buffer characters to ints
   
   
        #========== Get PORT/TRIS Registers ==========#
        # PORT Registers
        self.usb.control_transfer(self.dev, 0xC0, GET_REGISTERS, 0, 0, 8, self.buffer)
        self.PORTA = ord(self.buffer[0])
        self.PORTB = ord(self.buffer[1])
        self.PORTC = ord(self.buffer[2])
        
        self.TRISA = ord(self.buffer[3])
        self.TRISB = ord(self.buffer[4])
        self.TRISC = ord(self.buffer[5])

        self.update_gui()
        
        # Get the "debug led" status
        self.get_led_clicked() 



    #========== GUI & Variable Refresh (live monitoring) ==========#
        

    # Updates the gui display (here you can alter the screen text)
    def update_gui(self):
        
        self.led_label.setText("Led: %d" % self.led_status) #update GUI
        self.usb_msg2_label2.setText("(" + str(self.usb_msg2_input.sliderPosition()) + ")") 
        
        self.PORTA_label.setText("PORTA: %s" % bin(self.PORTA))
        self.PORTB_label.setText("PORTB: %s" % bin(self.PORTB))
        self.PORTC_label.setText("PORTC: %s" % bin(self.PORTC))
        
        self.TRISA_label.setText("TRISA: %s" % bin(self.TRISA))
        self.TRISB_label.setText("TRISB: %s" % bin(self.TRISB))
        self.TRISC_label.setText("TRISC: %s" % bin(self.TRISC))
        
        self.debug_message0_label.setText("Debug Msg0: %d" % self.debug_message[0])
        self.debug_message1_label.setText("Debug Msg1: %d" % self.debug_message[1])
        self.debug_message2_label.setText("Debug Msg2: %d" % self.debug_message[2])
        self.debug_message3_label.setText("Debug Msg3: %d" % self.debug_message[3])
        self.debug_message4_label.setText("Debug Msg4: %d" % self.debug_message[4])
        self.debug_message5_label.setText("Debug Msg5: %d" % self.debug_message[5])
        self.debug_message6_label.setText("Debug Msg6: %d" % self.debug_message[6])
        self.debug_message7_label.setText("Debug Msg7: %d" % self.debug_message[7])

        
        
        
                                    # =====      Other Methods       ===== #
        
    
    # The threaded loop that constantly communicates with PIC (getting and sending data)
    def main_loop(self):
        
        while self.live_monitoring == 1: # Cycle through the various variables we're monitoring 
            self.get_pic_status()
            self.update_gui()

            time.sleep(1.0/self.refresh_rate)
            
        print "stopped live monitoring"

        
    # Used to save the PIC state to a text file
    def log_data(self, duration):
        
        if (duration != 1):                             # if have to log
            self.data_logging = not self.data_logging   # reverse status
            if (not self.data_logging):                 # if not logging, quit
                return
                
        print "Beginning to log data.." 
        
        # Initialize Plot Visualization
        self.plot_visualization = Continual_Plot.ContinualPlot()
        
        # Figure out time
        now = datetime.datetime.now()
        now_s = "%d.%d.%d - %dh.%dm.%ds" % (now.month, now.day, now.year, now.hour, now.minute, now.second)
        
        # Name file
        if (duration == 1):
            filename = "%s\\data\\data - %s - single data log.txt" % (os.getcwd(), now_s)
        else:
            filename = "%s\\data\\data - %s - continual data log.txt" % (os.getcwd(), now_s)
        
        # Make output directory (unless already exists)
        dataLogger.makeDir()
        
        # Open File
        print "Writing to file: %s" % filename
        fout = open(filename, 'w')
        
        # Write starting data/time
        fout.write("Start time: %s\n\n\n" % now_s)
        
        # Write Column headers
        #fout.write(dataLogger.makeHeaders())
        
        # Either run once, or start thread (depending on run specs)
        if (duration == 1):
            self.log_data_write(fout)
            fout.close()
            print "Finished logging PIC state"
            self.statusBar.showMessage("Finished logging PIC state")
        else:
            if (self.data_logging):
                thread.start_new_thread(self.log_data_thread, (fout,))
                self.statusBar.showMessage("Started Live data logging")
            



    # Sub-method of logging data. Gets variables, formats them, and writes them
    def log_data_write(self, fout):
        
        """
        # Store all printed vals in an array
        s = [self.PORTA, self.PORTB, self.PORTC, self.TRISA, self.TRISB, self.TRISC]
        s.extend(self.debug_message)
        
        # Create formatted write string
        sout = dataLogger.format_output(s)
        """
        
        # Read and convert 2 bytes to one ADC val.. then to a voltage
        adc_read_val = ConversionFunctions.convert8bitTo16bit(high_byte = self.debug_message[3], low_byte = self.debug_message[6])
        adc_read_voltage = ConversionFunctions.adcToVoltage(adc_read_val)
        
        # sends value to the visualization plot
        self.plot_visualization.addData(adc_read_voltage)
        
        # Write string to file
        fout.write("%.3f" % adc_read_voltage)
        fout.write("\n")
        
        
    # Sub-method of logging data. An infinite loop that will run until user disengages it
    def log_data_thread(self, fout):
        
        while(self.data_logging):
            # Write data
            self.log_data_write(fout)
            
            # Wait for program to catch up
            time.sleep(1.0/self.refresh_rate)
        
        self.plot_visualization.exit()
        fout.close()
        print "Stopped live data logging"
        self.statusBar.showMessage("Stopped live data logging")
        
        
        
    # Pops up a menu to let the user alter the refresh rate
    def change_refresh_rate(self):
        input, ok = QtGui.QInputDialog.getText(self, 'Set new value', 'Set new refresh rate (#updates/sec) \nMin: 1, Max: 66')
        
        if ok:                                      # if user hits ok
            try:                                    # Check that it's a number
                input = int(input)
            except:
                print "sorry I need a number there"
            
            if input >= 1 and input <= 66:          # Check number's value
                self.refresh_rate = input
                self.statusBar.showMessage("Now checking PIC's status {0} times/second".format(input))
        
    
    
    # Try opening documentation in wordpad. If fails, open in notepad
    def launch_documentation(self):
        
        success = False
        
        try:
            os.system("write.exe ..\\Documentation\\Documentation.rtf")
            success = True
        except:
            pass
            
        if not success:
            try:
                os.system("wordpad.exe ..\\Documentation\\Documentation.rtf")
                success = True
            except:
                pass
                
        if not success:
            try:
                os.system("notepad ..\\Documentation\\Documentation.txt")
                print "The documentation is also available in nicely formated .rtf format."
                print "I couldn't open it with wordpad however, but you're free to try yourself!"
            except:
                print "The documentation is located under the 'documentation' folder."
                print "I couldn't open it with either wordpad nor notepad, but you're free to try!"



# ========== General Functions ========== #
    
# Takes the inverse of a 0/1
def inverse(inverseOf):
    if (inverseOf == 1):
        return 0
    else:
        return 1



# Initializes the GUI
if __name__=="__main__":
    # GUI Init
    app = QtGui.QApplication(sys.argv)
    gui = GuiInit()
    gui.show()
    
    
    # End
    #gui.usb.close_device(self.dev)
    sys.exit(app.exec_())
    gui.usb.close_device(self.dev)
    
    
"""
This work is licensed under the Creative Commons Attribution 3.0 United States License. To view a copy of this license, visit http://creativecommons.org/licenses/by/3.0/us
"""