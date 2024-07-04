QPI
:5 3 0 F8
 
System setting
---------------
read system time
05 03 17 8E 00 06 A1 D3
Set system time: (2024-04-11 19:19:53)
05 10 17 8E 00 06 0C 07 E8 00 04 00 0B 00 13 00 13 00 35 15 AE


Read: Clear All Historical Power Generation
05 03 13 89 00 01 50 E0
Write:
05 06 13 89 00 01 9C E0


Grid setting
--------------
AC Input Range
05 03 13 9B 00 01 F0 E5
Set:
- appliance: 05 06 13 9B 00 00 FD 25
- UPS:  05 06 13 9B 00 01 3C E5


Battery setting
----------------
Charger Source Priority
05 03 13 99 00 01 51 25 
Set:
- solar priority: 05 06 13 99 00 00 5C E5  
- solar & utility: 05 06 13 99 00 01 9D 25
- solar only: 05 06 13 99 00 02 DD 24
 resp for solar only: 05 03 02 00 02 C8 45
 
Max Total Charge Current
05 03 13 9E 00 01 E0 E4
Set:
- 10A: 05 06 13 9E 00 0A 6D 23
- 30A: 05 06 13 9E 00 1E 6D 2C
- 160A: 05 06 13 9E 00 A0 ED 5C

Max Utility Charge Current
05 03 13 A0 00 01 81 28
Set:
 - 2A: 05 06 13 A0 00 02 0D 29
 - 20A: 05 06 13 A0 00 14 8C E7
 - 100A: 05 06 13 A0 00 64 8D 03 

Battery Type
05 03 13 9C 00 01 41 24
Set:
 - AGM: 05 06 13 9C 00 00 4C E4 
 - flooded: 05 06 13 9C 00 01 8D 24
 - user: 05 06 13 9C 00 02 CD 25
 - LIB:  05 06 13 9C 00 03 0C E5
 
Bulk Charging Voltage
25.0~31.5(24V) 48.0~61.0(48V)
05 03 13 A3 00 01 71 28
 Set 56.3V: 05 06 13 A3 02 33 3D 9D


Floating Charging Voltage
25.0~31.5(24V) 48.0~61.0(48V)
05 03 13 A4 00 01 C0 E9
 Set 54.6V: 05 06 13 A4 02 22 4C 50

Low Battery Cut-off Voltage
20.0~24.0(24V) 40.0~48.0(48V)
05 03 13 A5 00 01 91 29 
 Set 42.0V: 05 06 13 A5 01 A4 9C C2

Comeback utility mode voltage point (SBU priority)
21.0~25.5(24V) 42.0~51.0(48V)
05 03 13 A1 00 01 D0 E8
 Set 43.0V: 05 06 13 A1 01 AE 5D 04

Comeback battery mode voltage point (SBU priority)
24.0~29.0(24V) 48.0~58.0(48V)
05 03 13 A2 00 01 20 E8
 Set 52.0V: 05 06 13 A2 02 08 2D 8E


Battery Equalization
05 03 13 93 00 01 71 27
 Set:
 - prohibited: 05 06 13 93 00 00 7C E7
 - enabled: 05 06 13 93 00 01 BD 27

Battery Equalization Voltage
25.0~31.5(24V) 48.0~61.0(48V)
05 03 13 A6 00 01 61 29
 set 58.0V:  05 06 13 A6 02 44 6D BA

Battery Equalized Time
5min~900min
05 03 13 A7 00 01 30 E9
 set 60min: 05 06 13 A7 00 3C 3D 38 
 
Battery Equalized Timeout
5min~900min
05 03 13 A8 00 01 00 EA
 set 120min: 05 06 13 A8 00 78 0D 08

Battery Equalization Interval
0~90days
05 03 13 A9 00 01 51 2A
  set 30days: 05 06 13 A9 00 1E DC E2 
  
Battery Equalization Activated Immediately
05 03 13 94 00 01 C0 E6 
 set:
 - prohibited: 05 06 13 94 00 00 CD 26
 - enabled: 05 06 13 94 00 01 0C E6

Accumulator setting
Buzzer Alarm
05 03 13 8A 00 01 A0 E0
 set:
 - prohibited: 05 06 13 8A 00 00 AD 20
 - enabled: 05 06 13 8A 00 01 6C E0

Beeps While Primary Source Interrupt
05 03 13 8F 00 01 B0 E1
 set:
 - prohibited:  05 06 13 8F 00 00 BD 21
 - enabled: 05 06 13 8F 00 01 7C E1


LCD Backlight
05 03 13 8C 00 01 40 E1
 set:
  off: 05 06 13 8C 00 00 4D 21
  on: 05 06 13 8C 00 01 8C E1

Return To The Main LCD Page
05 03 13 90 00 01 81 27 
  set:
   off: 05 06 13 90 00 00 8C E7
   on: 05 06 13 90 00 01 4D 27 

Power Saving Mode
05 03 13 8B 00 01 F1 20
 set:
  - off: 05 06 13 8B 00 00 FC E0
  - on: 05 06 13 8B 00 01 3D 20 
  resp for enabled: 05 03 02 00 01 88 44
  
Over Temperature Auto Restart
05 03 13 8E 00 01 E1 21
 set:
  off: 05 06 13 8E 00 00 EC E1
  on: 05 06 13 8E 00 01 2D 21

Record Fault Code
05 03 13 92 00 01 20 E7
 set:
   - off: 05 06 13 92 00 00 2D 27
   - on: 05 06 13 92 00 01 EC E7    

Restore Defaults
05 03 13 98 00 01 00 E5 
 set:
  - off: 05 06 13 98 00 00 0D 25
  - on: 05 06 13 98 00 01 CC E5 
  
Load setting
-------------
Output Source Priority
05 03 13 9A 00 01 A1 25
 set:
  - utility: 05 06 13 9A 00 00 AC E5
  - solar: 05 06 13 9A 00 01 6D 25
  - SBU: 05 06 13 9A 00 02 2D 24
  resp for mKs: 05 03 02 00 03 09 85
  
Output Voltage
05 03 13 9F 00 01 B1 24
 set 230V:  05 06 13 9F 00 E6 3D 6E
 

Output Frequency
05 03 13 9D 00 01 10 E4
 set:
  - 50hz: 05 06 13 9D 00 00 1D 24
  - 60hz: 05 06 13 9D 00 01 DC E4

Overload Auto Restart
05 03 13 8D 00 01 11 21
 set:
  - off: 05 06 13 8D 00 00 1C E1
  - on: 05 06 13 8D 00 01 DD 21

Transfer To Bypass Overload
05 03 13 8D 00 01 11 21
 set:
  - off: 05 06 13 91 00 00 DD 27 
  - on: 05 06 13 91 00 01 1C E7 

Other setting
-------------
GRID-tie operation
05 03 13 AA 00 01 A1 2A
 set:
  - off: 05 06 13 AA 00 00 AC EA
  - on:  05 06 13 AA 00 01 6D 2A 
 resp for mKs?: 05 03 02 05 61 8B 3C

GRID-tie current
05 03 13 AB 00 01 F0 EA
 set:
  - 2A: 05 06 13 AB 00 01 3C EA
  - 4A: 05 06 13 AB 00 02 7C EB
  - 6A: 05 06 13 AB 00 03 BD 2B
  - 28A: 05 06 13 AB 00 0E 7C EE
  - 30A: 05 06 13 AB 00 0F BD 2E 
 resp for mKs?: 05 03 02 00 0s0 49 84

Led pattern light
05 03 13 AC 00 01 41 2B
 set:
  - off: 05 06 13 AC 00 00 4C EB
  - on: 05 06 13 AC 00 01 8D 2B 
  resp for mKs?: 05 03 02 00 0A C9 83
  
Dual output
05 03 13 AD 00 01 10 EB
 set:
  - off: 05 06 13 AD 00 00 1D 2B
  - on: 05 06 13 AD 00 01 DC EB
  
Enter the dual output functional vltage point
05 03 13 AE 00 01 E0 EB
 set:
  - 54.0V: 05 06 13 AE 02 1C ED 82
  
