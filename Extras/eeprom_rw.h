
	#ifndef _EEPROM_rw_H_
	#define _EEPROM_rw_H_

	unsigned char InitEEPROM();
	unsigned char eeprom_write_byte(unsigned char address, unsigned char data);
	unsigned char eeprom_read_byte(unsigned char);

	#endif
