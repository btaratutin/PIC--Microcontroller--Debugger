/*
    Functions in the usb_code.c file that must be accessable externally.
    Necessary in order for the usb_code.c to be abstracted out properly
*/

#ifndef h_usb_defs_extern
#define h_usb_defs_extern

	//functions and variables that are called externally
	void InitUSB(void);				
	void ServiceUSB(void);

#endif