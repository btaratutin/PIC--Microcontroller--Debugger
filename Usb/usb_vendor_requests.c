#include <p18f2455.h>
#include "usb_vendor_requests.h"




#define	GET_LED			0x03		// vendor-specific request to read RA2
#define SET_LED			0x04		// vendor-specific request to set the duty cycle of the blinking LED on RA0
#define GET_MSG			0x0A		// sends debug vals to 10

// Extern Vars
unsigned char debug_message;

unsigned char * ProcessVendorRequests(unsigned char vendor_request, unsigned char bufferReturn[])
{
	// buffer Return passed in externally
	
	/*
		BD0I.address[0] = bufferReturn[0];
		BD0I.bytecount = bufferReturn[1];
		BD0I.status = bufferReturn[2];
		USB_error_flags = bufferReturn[3];
	*/
	
	
	/*
		USB_buffer_data: the setup packet that the USB host sends to initiate connection
			- bmRequest type 	(1)			Input or Output, plus request type (0b1 100 0000) = input, vendor request, something else ||| (0b0 100 0000) = output, vendor, etc.
			- bRequest			(1)			Which thing should get called (we decide)
			- wValue, wValueHi	(2)			Data sent from USB host to PIC
			- wIndex			(2)			
			- wLength			(2)			Whether expecting data back or not
	*/
	
	/*
		Once we have recieved the setup packet, we populate the buffer that the host device created (BD0I) (the 'I' has something to do with Input)
		Thus, you can set the buffer address to contain the value you want to send
	
	*/
	
	
	switch (vendor_request) 
	{
		case SET_LED:
			//LED = !LED;
			//USB_buffer_data[wValue]	// Data sent from USB to PIC
			//USB_buffer_data[wValueHi]	// Data sent from USB to PIC
			bufferReturn[1] = 0x00;		// set EP0 IN byte count to 0
			bufferReturn[2] = 0xC8;			// send packet as DATA1, set UOWN bit
			break;

		case GET_LED:
			bufferReturn[0] = (1) ? 0x01:0x00;	// if RA2 is high, put 0x01 into EP0 IN buffer, else put 0x00 into EP0 IN buffer
			bufferReturn[1] = 0x01;		// Can send up to 8 bytes on low-speed USB
			
			/*
			BD0I.address[0] = 1
			BD0I.address[1] = 15
			BD0I.address[2] = 33
			
			BD0I.bytecount = 0x03;		// Can send up to 8 bytes on low-speed USB
			*/
			bufferReturn[2] = 0xC8;			// send packet as DATA1, set UOWN bit
			break;
			
		case GET_MSG:
			bufferReturn[0] = debug_message;		
			bufferReturn[1] = 0x01;					// set EP0 IN byte count to 1
			bufferReturn[2] = 0xC8;						// send packet as DATA1, set UOWN bit
			break;
			
		default:
			bufferReturn[3] |= 0x01;	// set Request Error Flag
			
	}
	
	return(bufferReturn);
}