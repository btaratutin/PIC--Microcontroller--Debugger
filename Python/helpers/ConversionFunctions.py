# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 10:02:37 2010

@author: btaratutin
"""

# Convert 2 8-bit values into a 16-bit value
def convert8bitTo16bit(high_byte, low_byte):
    return ( (high_byte << 8) + low_byte )

# convert "adc_values" to voltages
def adcToVoltage(adc_val):
    Vref = 2.5
    LSB = Vref / 1024
    voltage = round(adc_val * LSB - Vref, 3)
    return voltage
    #(to string)return '%.3f' % voltage