/*
	Boris Taratutin
	11.14.2009
	
	General:
		Some code for testing & debugging PICs and circuits.
		Most useful because of the easy connection to the USB; allows for easy USB printout of stored variables
	
	Use:	
		Just set the various values of debug_message (0-7) to whatever values you want sent to the USB, and they will be read out via the python code
	
	Notes: 
		PIC cannot (on its own accord) send commands to the computer via usb. The computer must instead request information from the Pic, and then the Pic can send commands.
*/

#include <p18f2455.h>
#include "configs.h"


// Externals
#include "main.h"				// Contains vendor request associations (for USB)
#include "usb/usb_defs_extern.h"		// Externaly-necessary definitions; for initializing USB and processing commands
#include "extras/ad_converter.h"		// Simple script for a simple a/d conversion

#include "extras/eeprom_rw.h"			// For writing & reading from the PIC's permanent data storage (retained after powerdown)


// Extern Vars
unsigned char debug_message[] = {0, 0, 0, 0, 0, 0, 0, 0};	// The array whose values you should set to whatever debug messages you want


// Definitions
#define DEBUG_LED 	PORTCbits.RC7				// Always good to have test light (#define allows us to rename the pin to something more meaningful)
#define BLINKY_LED 	PORTAbits.RA1				// LED that will blink
#define FADY_LED	PORTAbits.RA2				// LED whose brightness can be changed

// Reg Vars
unsigned char pot_value;						// obtained from potentiometer
unsigned char blink_value = 127;				// obtained from usb signal
unsigned char light_value = 127;				// obtained from usb signal

unsigned char eeprom_write_to 	= 0;			// EEPROM address to write to next
unsigned char eeprom_error		= 0;			// Whether an error occured writing to eeprom
unsigned char eeprom[8];


// Pin States Diagram (makes it easy to see what pins are used for what!)

//           +-------------- RA7 (0) =
//           |+------------- RA6 (0) =
//           ||+------------ RA5 (0) = 
//           |||+----------- RA4 (0) = 
//           ||||+---------- RA3 (0) = 
//           |||||+--------- RA2 (0) = Pulsy LED
//           ||||||+-------- RA1 (0) = Blinky LED
//           |||||||+------- RA0 (I) = Potentiometer


//           +-------------- RB7 (0) = 
//           |+------------- RB6 (0) = 
//           ||+------------ RB5 (0) = 
//           |||+----------- RB1 (0) = 
//           ||||+---------- RB1 (0) = 
//           |||||+--------- RB2 (0) = 
//           ||||||+-------- RB1 (0) = 
//           |||||||+------- RB0 (0) = 


//           +-------------- RC7 (0) = 
//           |+------------- RC6 (0) = 
//           ||+------------ RC5 (0) = 
//           |||+----------- RC4 (0) = 
//           ||||+---------- RC3 (0) = 
//           |||||+--------- RC2 (0) = 
//           ||||||+-------- RC1 (I) = Button/Switch
//           |||||||+------- RC0 (0) = Debug LED
	

void main(void) {

	unsigned char i;

    // Clear all ports
    PORTA = 0b00000000;
    PORTB = 0b00000000;
    PORTC = 0b00000000;
    
    // Initialize Input/Output Registers
    TRISA = 0b00000001;
    TRISB = 0b00000000;
    TRISC = 0b01000000;
    
    //Initialize A/D Converters
    ADCON0 = 0b00000001;			// select AN0, enable A/D module
    ADCON1 = 0b00001101;			// set up RA0/AN0 & RA1/AN1 as an analog input and set up RA2..RA5 as digital I/Os
    ADCON2 = 0b00101110;			// configure A/D module result to left justified, acquisition time to 32 us, and clock period to 2.67 us
    
    // Initialize Timers
    T0CON = 0b10000101;				// initialize Timer0 to go off every 700 ms
    
    // Other Init Functions
    InitUSB();						// initialize the USB registers and serial interface engine
    ServiceUSB();
    
    
	debug_message[7] = InitEEPROM();// Eeprom_rw function. Tests EEPROM and inits vals to 0	

	
    // Main loop	
    while (1) 
    { 
    	ServiceUSB(); 							// service any pending USB requests
    	
		// Simple: if button pressed, change LED status
	   	if (PORTCbits.RC6 == 1)						
	   	{
	    	DEBUG_LED = !DEBUG_LED;
	    	Delay10TCYx(200);
		}
		    
		
		pot_value = ADConversion(0);					// Read value of POT (connected to RA0)
		
		
		// Blinking/Fading lights (both the blink_value and light_value are set via the usb_gui)
		BLINKY_LED = (TMR0H < blink_value) ? 1:0;			// ...set RA1 high if the high byte of the Timer0 register is less than POT_VALUE, else clear RA1,...
		FADY_LED = (TMR0L < light_value) ? 1:0;				// Using the low register of the timer essentially PWMs this LED, allowing you to regulate its brightness
		
		
		// Set the usb messages to whatever values you want to send back to the debug gui
		debug_message[4] = TMR0H;
		debug_message[5] = TMR0L;
		//debug_message[7] = eeprom_error;
		
	    
    }							
    
}








/*=======================================================================================================================

	Vendor Requests

  =======================================================================================================================*/

/*
    Code for processing the requests received from the USB
*/

// Vendor Request defines (set an arbitrary number for a function to be carried out) (need to match the ones in the python gui)
#define	GET_LED			3		// vendor-specific request to read RA2
#define SET_LED			4		// vendor-specific request to set the duty cycle of the blinking LED on RA0

#define GET_MSG			10		// sends debug vals to 10
#define GET_REGISTERS 	11		// Get PORT & TRIS Registers
#define GET_EEPROM		12		// Sends the EEPROM (all 256 bytes)

#define SET_USB_MSG1	20		// USB sends message1 to PIC
#define SET_USB_MSG2	21		// USB sends message2 to PIC

#define SET_PORTA       30		// USB sets PORTA
#define SET_PORTB       31		// USB sets PORTB
#define SET_PORTC       32		// USB sets PORTC

#define SET_TRISA       35		// USB sets TRISA
#define SET_TRISB       36		// USB sets TRISB
#define SET_TRISC       37		// USB sets TRISC


// Variables
#define bytes_to_send	bufferSettings[0]

unsigned char eeprom_return_index = 0;



// Once the PIC usb_code receives a command from the usb, it will call this function
void ProcessVendorRequest(unsigned char vendor_request, unsigned char data_from_usb, unsigned char bufferSettings[], unsigned char returnData[])
{
    /*
	This function then runs the usb command through a case/switch statement and selects the appropriate actions to take
	However, it is abstracted and simplified a bit from the original USB output. To understand more, open up "usb_code.c"
	and scroll down to the near bottom to a section titled "vendor requests". That has a more thorough explanation there.
    */
    /*
	Passed-In Variables explanation
	
	vendor_request:		The number of the vendor request. Should match the definitions above. Cycled through to select correct action.
	data_from_usb:		If the USB sent any data, that value will be stored here
	bufferSettings[]:	Some settings for the buffer (see lower)
	returnData[]:		If you want to return any data to the USB, store the values in this array
    */
    /*
	    bufferSettings[0] 		--> 		BD0I.bytecount		(# bytes to send back to USB)
	    bufferSettings[1]		--> 		BD0I.status			(default value already set at 0xC8 - so dont change unless need to)
	    bufferSettings[2]		-->			USB_error_flags		(got an error? set this to 1)
    */
    /*
	Though this method is technecally 'void', modifying any of the arrays passed in (bufferSettings, returnData)
	Will modify their contents, since they are pointers.
    */
	
	unsigned char i, j;
	
	
	// Cycles the received vendor request against the possible ones, to select the right action to take
	switch (vendor_request) 
	{
		case SET_LED:									
			DEBUG_LED = data_from_usb ? 0x01:0x00;			// Sets the state of the LED to what the USB says
			bytes_to_send = 0x00;							// Set command, therefore don't send anything back		
			break;

		case GET_LED:
			returnData[0] = (DEBUG_LED) ? 0x01:0x00;		// if RA2 is high, put 0x01 into EP0 IN buffer, else put 0x00 into EP0 IN buffer
			bytes_to_send = 0x01;							// # bytes to send
			break;
			
		case GET_MSG:	
			bytes_to_send = 0x08;							// #bytes to send
			
			// Cycles through the debug_message & sends its values off to the computer via usb
			for (i = 0; i < bufferSettings[0]; i++)
			{
				returnData[i] = debug_message[i];
				//returnData[i] = eeprom[i];
			}
			break;

		case GET_REGISTERS:									// Returns the values of the PIC's registers
			bytes_to_send = 0x06;
			returnData[0] = PORTA;
			returnData[1] = PORTB;
			returnData[2] = PORTC;
			
			returnData[3] = TRISA;
			returnData[4] = TRISB;
			returnData[5] = TRISC;
			break;
			
		case GET_EEPROM:
			bytes_to_send = 0x08;							// #bytes to send
			
			// Cycles through the debug_message & sends its values off to the computer via usb
			for (i = 0; i < 8; i++)
			{
				returnData[i] = eeprom_read_byte(eeprom_return_index);
				eeprom_return_index++;
			}
			break;
						
			// Increment and check new index
			if (eeprom_return_index > 255)
				eeprom_return_index = 0;
			
			break;
			
		case SET_PORTA:										// Sets the appropriate register to the given value
			PORTA = data_from_usb;
			break;
		
		case SET_PORTB:
			PORTB = data_from_usb;
			break;
		
		case SET_PORTC:
			PORTC = data_from_usb;
			break;
		
		case SET_TRISA:
			TRISA = data_from_usb;
			break;
		
		case SET_TRISB:
			TRISB = data_from_usb;
			break;
		
		case SET_TRISC:
			TRISC = data_from_usb;
			break;
			
		case SET_USB_MSG1:									// Data sent from usb can be assigned to a variable
			//blink_value = data_from_usb;
			eeprom_error = eeprom_write_byte(eeprom_write_to, data_from_usb);
			
			eeprom_write_to++;
			if (eeprom_write_to > 4)
				eeprom_write_to = 0;
				
			DEBUG_LED = !DEBUG_LED;
			
			debug_message[7] = eeprom_error;
				
			break;
			
		case SET_USB_MSG2:									// Data sent from usb can be assigned to a variable
			//light_value = data_from_usb;
			break;
		
			
		default:
			bufferSettings[3] |= 0x01;				// If this statement is reached, something went wrong!
			
	}
	
}