
#ifndef h_main
#define h_main

	// Functions Called Externally
	void ProcessVendorRequest(unsigned char, unsigned char, unsigned char[], unsigned char[]);
	
	// Functions that might be called externally
	unsigned char getPotentiometerVal(void);
	
	// Variables Called Externally
	extern unsigned char debug_message[];

#endif