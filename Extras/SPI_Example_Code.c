/*
	Boris Taratutin	& Carl Tappan
	10.26.10
	
	Questions? 						[boris.taratutin@gmail.com]
*/

#include <p18f2455.h>				// Header file for your PIC (we're using 18f2455)
#include <spi.h>					// Microchip SPI library file - makes all this possible!
#include "h_SPI_Example_Code.h"		// Header file (has function prototypes, etc.)

/*
What is SPI?

SPI stands for "Serial Peripheral Interface", and is a common 4-wire protocol used by PICs to talk
to other devices (such as external ADCs, motor drivers, or even other PICs!).

At the very general level, SPI involves sending a string of digital bits between two chips - one the
"master" (which is your PIC), and one the "slave" (the receiving device). If you buy a chip (like an external
ADC) that has an SPI interface, the datasheet should describe the specific protocol that makes that device operate.
For example, to initialize the ADC, you may need to send it a value of 255 (0xff, 0b11111111), and to have it take
a sampling (initialize an AD conversion), you may need to send it a value of 182 (0xB6, 0b10110110) [your numbers will be different].

The section below details the PIC-specifics that you need to know to get SPI up and running, and includes sample code
for actually sending values via SPI, which turns out to be pretty easy to do using Microchip's SPI library
*/


/*
General Idea of SPI operation: 

There are 3 common pins - SDO, SDI, SCK (described below). These are connected to every "slave" device (usually,
this is some sort of chip - like an external ADC, a motor controller, etc.). This is where the beauty of SPI comes in - 
since you can have a large number of devices (say, 20) connected to your PIC, and they would all share the same 3 wires

Then, there are "Slave Select" or "Chip Select" pins - these can be anything you'd like (you define them).
Ie. you can use PORTAbits.RA0, or PORTCbits.RC2. Your call. These pins are used to "select" the device you are working  with -
which is important to do since you may have up to 20 devices connected on the same SDO/SDI/SCK lines.

Usually, slave devices are what's known as "Active Low". That means they "turn on" when you set their SS pin to 0.
Thus, if you want to talk to a device, you simply set its SS pin to 0 and set other devices' pins to 1.

If you only have device, you can just always have it selected (always have its pin at 0).

Lastly, the clock signal (SCK) pin is used by the devices to synchronize the signals. Once you make sure your clock rate
is within the acceptable rates of the slave device, then you don't have to worry about the SCK line.

Note: this code is for the <hardware> SPI implementation - which is tied to specific PIC hardware pins. This is typically
the type of SPI that you want to be using
*/

// Specific to PIC18f2455 Configuration (change the pins based on your PIC type/data sheet)
// Define names for the various SPI pins. 
#define SDO 		PORTCbits.RC7			// Serial Data Out (SDO)	-- Pin that data goes out from	(common to all devices)
#define SDI 		PORTBbits.RB0			// Serial Data In (SDI)		-- Pin that data comes in to	(common to all devices)
#define SDI_DIR 	TRISBbits.TRISB0		// Direction of SDI signal  -- You want to be able to set it as an "input" since you're 
#define SCK 		PORTBbits.RB1			// Serial Clock (SCK)		-- Pin that sends a clock signal that synchronizes all  SPI devices	(common to all devices)

// Here, you define your various "Slave Select" pins. These can be whatever general I/O pin you'd like
#define SS  		PORTAbits.RA4			// Slave Select (SS)		-- Pin that selects which "slave" module you are communicating with

#define select 		0						// Since most devices are "active low", define "select" as 0
#define deselect	1


// Initializes an SPI connection
void InitSPI() 
{	
	SDI		= 0;					// Just in case, reset SDI pin value
	SDI_DIR = 1;					// Set serialIn High (pull not_CS high.)
	
	OpenSPI(SPI_FOSC_4, MODE_00, SMPEND);	//Open a SPI module (Code within spi.h)
}

// Writes a value to the SPI
void WriteSomething(unsigned char val)
{
	INTCONbits.GIE = 0;				// Disable Global Interrupts (so an interrupt doesn't mess up your SPI communication)
	SS = select;					// Select Device

	putcSPI(val);					// Writes one byte to the spi
	putcSPI(213);					// Writes another byte to the SPI port				
	// p.52 of Microchip C18 Libraries Datasheet

	SS = deselect;					// Deselect Device
	INTCONbits.GIE = 1;				// Enable interrupts again
}

// Sample function that simpulates "requesting" a byte of data from an ADC
void RequestAByte()
{
	unsigned char read_request = 0b10011010;	// Dummy protocol value for asking the ADC to send us a value
	SS = select;					// Select Device
	putcSPI(read_request); 			//send the ADC a request to read us a value. When it receives this cmd, wil lsend us a val
	getcSPI(); 						//read data byte. [keeps reading until gets an entire byte of data].
	SS = deselect;					// Deselect Device	
}	

// Simple example - sets up the SPI and then sends a value to it.
void main(void)
{
	PORTA = 0;						// Reset all of the PORT Registers
	PORTB = 0;
	PORTC = 0;

	TRISA = 0;						// Reset all of the TRIS registers
	TRISB = 0;
	TRISC = 0;

	ADCON1 = 0b00001111;			// Make sure ADC inputs all set to "digital"

	InitSPI() ;						// Initialize SPI connection

	while(1)
	{
		PORTCbits.RC0 = 1;			// Test pin (always have a test pin!)
		WriteSomething(0b10101011); // Output 0b10101011 on your SPI pin
	}
	
	
}