// Boris Taratutin - Nov. 1, 2009

 #include "eeprom_rw.h"
 #include <p18f2455.h>
/*
	Generalized code that can read/write to/from EEPROM
	
	Relevant Data Sheet Page: 91
	
	General Flow:
		1. Disable Interrupts
		2. Enable R/W (EECON1)
		3. Set address & data 
		4. Disable R/W
		5. Disable Interrupts
		
	Notes:
		- EEPROM size is 256 bytes
		
*/

// Tests EEPROM and inits vals to 0	
unsigned char InitEEPROM()
{
	unsigned char i;
	unsigned char errors;
	
	for (i = 0; i < 255; i++)				// For some reason, complains if <= 255 or < 256...
	{
		// Check if eeprom is reading and writing correctly
		eeprom_write_byte(i, 0x55);
		if (eeprom_read_byte(i) != 0x55)
			errors++;

		eeprom_write_byte(i, 0);			// Set default value to 0
	}
	
	eeprom_write_byte(255, 0);
	
	return errors; 							// Return # of errors
}	
    
unsigned char eeprom_write_byte(unsigned char address, unsigned char data)	// Write to EEPROM
{
	unsigned char error_flag = 0;		// 1 = error occured. 0 = everything went well
	
	//	How writing works...
	/*
		1. Enable writing (EECON1)
		2. Set address & data 
		3. Disable writing
	*/
	
	//dont want to be interrupted while writing eeprom; can damage memory. Therefore, disable all interrupts
	INTCONbits.GIE = 0; 				// Gen. interrupt disable; timer, ad converter, serial, etc.
	EECON1 = 0b00000100; 				// Allow write cycles
	
	//Set what and where to write
	EEADR = address; 					// Address of value to store. Starts at 0.
	EEDATA = data; 						// The data that will be stored
	
	// Don't really know what these two do, but have two theories:
	// Theory 1: "combination lock" - to really ensure writing to eeprom
	// Theory 2: "error checker" - In binary, 0x55 = 01010101, 0xAA = 10101010. Thus setting the eeprom equal to x55, then xAA tests every bit and checks if it's working
	EECON2 = 0x55; 
	EECON2 = 0xAA; 
	
	//Initialize, write, and reset
	EECON1bits.WR = 1; 					// Initiates write operations. Set by software, cleared by hardware
	while (!PIR2bits.EEIF) {} 			// The flag that goes off when the write command is done
	PIR2bits.EEIF = 0; 					// Flag set by hardware, must be reset by software
	
	if(EECON1bits.WRERR){ error_flag = 1; }
	
	EECON1 = 0b00000000; 				// Stop writing
	INTCONbits.GIE = 1; 				// Enable interrupts again
	
	return error_flag;					// 1 = error occured. 0 = everything went well
}


unsigned char eeprom_read_byte(unsigned char address)	// Read from EEPROM
{
	INTCONbits.GIE = 0;					// Disable all interrupts; protects eeprom memory
	
	EECON1 = 0;							// Access EEPROM Memory, clears bits
	EEADR = address;					// Sets address to read from
	
	EECON1bits.RD = 1;					// Initiates reading
	
	INTCONbits.GIE = 1;					// Enable interrupts again

	return(EEDATA);
}