/*
	Boris Taratutin	& Carl Tappan
	11.06.10
	
	Questions? 						[boris.taratutin@gmail.com]
*/
 
#include <p18f2455.h>
#include "configs.h"


/*
The basics of Interrupts:

Interrupts are awesome, and on top of that, darn classy. They're the most robust and industry-standard way of executing code based on
an external event (pin high), or cyclically, based on one of the PIC's internal timers.

Typically, the 'easiest' way to execute events is via "polling" - ie. continually (in the main while(1) loop) checking inputs, and when one of them
changes to a certain state (ie. a timer overflows, or a pin goes high), executing code. However, this isn't very robust - instant reaction to an event isn't guaranteed
(ie. if you have method X executing, and your timer overflows and says "hey, it's time to send another puls). For applications where timing is essential 
(ie. communications) this isn't good enough. And that's where interrupts come in.

Interrupts allow you to program in various events (ie. timer0 overflow, or pin RB0 went high), and when that interrupt condition is met, whatever C code is currently
executing will be frozen by the interrupt routine, the interrupt routine will execute, and then your code will resume. If you want to do something like process a signal
when you get a rising edge on a pin, or blink an LED at a very specific frequency, this is a really powerful tool. Interrupts are also really useful in instances 
like if you want to turn on a motor when a button is pressed but.. at the same time, you need to continually service usb to avoid disconnicting, 
interrupts are your friends. 

You can generate an interrupt on a rising or falling edge of several pins, a timer overflow, a change of state on PORTB pins, or any other number of arcane things. 
The code below does both - it will blink one cyclically based on TMR0, and a second based on the state (rising edge) of RB0

And remember kids, the PIC datasheet is your friend.
*/

// Define variables
#define TEST_LED 	PORTCbits.RC0		// A test/debug LED - so we know if our code is working
#define TEST_LED2	PORTCbits.RC1		// A secondary test LED - for the hardware interrupt

unsigned char blinky 	= 1;		// A variable used to store the value of the LED (expl. of why later)
unsigned char blinky2	= 1;		// Used to control TEST_LED2

// Defining functions before their actual implementation is called "prototyping" functions
// With interrupts, this is a very important step, so the compiler knows this function exists, when linking the interrupt to the called function
void interruptFunc(void);				// Creates a "prototype" of the interrupt method


/*
The following code may seem a bit strange/arcane, but we'll walk you through what's going on, and why we need it:

#pragma code high_vector = 0x08
	- This line sets the interrupt vector address (in hardware memory). This will tell the PIC "when you get an interrupt, look at 
	  this particular address in memory". A necessary step for setting interrupts up
	- 0x08 is for the "high" priority interrupts. (0x18 is for low priority)
	- Since we're working with "high priority" interrupts, we want to efine it as 0x08

void highPriorityInterrupt (void) { _asm GOTO interruptFunc _endasm }
	- Kind of looks like a function, but it is really what's known as a "vector" definition,  which is simply an address in memory that points to a function
	- Because C has no "GOTO" function, we must switch to assembly for a moment (done using the _asm, _endasm markers), so we can use the "GOTO" pointer
	- Whenever any interrupt is called, this function-vector will be called. However, you really shouldn't put any other code in here - and instead
	  point it to another function that will process the interrupts
	  
Note: the "#pragma" designator is a signal to the compiler that there is some instruction that it should carry out before compiling
*/

#pragma code high_vector = 0x08	
void highPriorityInterrupt (void)			
{
	_asm GOTO interruptFunc _endasm
}



/*
The following code is where the interrupt actually gets processed. Here, it's your duty to...
	1. Figure out where the interrupt source came from
	2. Execute the appropriate code (without modifying I/O registers)
	3. Reset the interrupt flag (so the interrupt can happen again)
*/

#pragma code						// Tells the compiler to organize the pic's memory however it wants to (as opposed to specifying a specific address - like we did above for the high_isr vector)
#pragma interrupt interruptFunc 	// Designate the function "interruptFunc" as an interrupt handler
void interruptFunc(void)
{
	if(INTCONbits.T0IF==1)			// Check where the interrupt came from (in this case, timer0's interrupt overflow flag)
	{
		blinky = !blinky;			// Change the state of the blinky variable on each interrupt (make it blink)
		INTCONbits.TMR0IF=0;		// Reset the timer0 interrupt flag.	
	}
	
	else if(INTCONbits.INT0IF==1)	// Check where the interrupt came from (in this case, the external interrupt - a high on RB0)
	{
		blinky = !blinky;			// Change the state of the blinky variable on each interrupt (make it blink)
		INTCONbits.INT0IF=0;		// Reset the INT0 external interrupt interrupt flag.	
	}
	
	/*
	!Note: Within the interrupt routine, you <cannot> set I/O registers explicitly. ie. we can't say PORTBbits.RB0 = 1.
	That's why we have to use an intermediary variable (blinky), and later assign PORTBbits.RB0 = blinky in the main loop.
	*/
}

// Sets up all of the registers necessary for using interrupts
void SetupInterrupts(void)
{
	T0CON = 0b10000111;					// Initialize Timer0 to some value (Our code is for a Timer0-based interrupt - so it's important to make sure its configured)

	/* All interrupts have 3 control bits:
		- Enable Bit	: (...IE) : enable interrupt (allows program execution to branch to the interrupt vector address when the flag bit is set)
		- Priority Bit	: (...IP) : select high priority or low priority
		- Flag Bit		: (...IF) : indicates that an interrupt event occurred
	*/
	
	/* 		===== General Interrupt Configuration =====		*/
	INTCONbits.GIE 		= 1;			// Enable all interrupt sources (both peripheral interrupts, and timer-based interrupts)
	
	
	/* 		===== Timer0 Interrupt Enable =====		*/
	INTCONbits.TMR0IE 	= 1;            // Enable interrupt on Timer0 overflow
	INTCON2bits.TMR0IP 	= 1;			// Set timer0 to have "high" priority interrupt
	INTCONbits.TMR0IF 	= 0;			// Reset the timer0 interrupt flag
	
	
	/* 		===== External Interrupt on RB0 Enable =====	*/
	INTCONbits.INT0IE	= 1;			// Enable External Interrupts (on pin INT0 - which is PORTBbits.RB0)
	INTCON2bits.INTEDG0 = 1;			// Configure the external interrupt to interrupt on rising edge 
	INTCON2bits.RBPU 	= 1;			// Disables all PORTB pull-ups
	INTCONbits.INT0IF	= 0;			// Reset the external interrupt flag bit
	// Note: the INT0 external interrupt is always "high priority", so we don't have to (and can't) set its interrupt priority

}	

void main (void)
{
	TRISA = 0;					// Set pins to outputs
	TRISB = 0;					// Set RB0 as an output (necessary for the interrupt routine)
	TRISC = 0;
	
	PORTA = 0;					// Reset Pin Values	
	PORTB = 0;
	PORTC = 0;
	
	ADCON1 = 0b00001111;		// Make sure ADC inputs all set to "digital"
	
	SetupInterrupts();			// LOOK HERE. This is where the magic happens - for configuring interrupts
	

	while (1)
	{
		TEST_LED  = blinky;		// Set the value of the TEST_LED to the value of our "blinky" variable - which is set by interrupts
		TEST_LED2 = blinky2;	// Likewise for TEST_LED2
	}
}