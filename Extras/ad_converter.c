/*
	Boris Taratutin
	11.14.2009
	
	Simple 'modularized' function for simple A/D converters.
	Instead of having to look up the values on the data sheet for the A/D converter, if you
	just want to do a conversion on pins RA0-RA4, just call this function and pass it the pin#
	And it will automatically run the A/D converter and return the result
	
	(doesnt work for v-ref or for pins not RA0...RA4)
*/


#include <p18f2455.h>
#include "ad_converter.h"

unsigned char ADConversion(unsigned char RA_Pin) // Takes an Analog Reading from a specified RX pin (assumes TRIS is already set)
{
	ADCON2 = 0b00101110;						// configure A/D module result to left justified, acquisition time to 32 us, and clock period to 2.67 us
	ADCON1 = (14-RA_Pin);						// (bits 0-3 set) Enables the enough pins as A/D to include given pin for the A/D conversion
	ADCON0 = (RA_Pin << 2) + 0b11;				// Sets the given pin as the A/D pin, and initiates the A/D conversion
	while (ADCON0bits.GO_DONE==1) {}			// Do nothing until the A/D conversion is done
	return ADRESH;								// Return A/D result
}