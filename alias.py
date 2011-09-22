#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Trbot3

Copyright (C)2008 Petr Nohejl, jestrab.net

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

This program comes with ABSOLUTELY NO WARRANTY!
"""



### IMPORT #####################################################################

import string 	# retezce

import alias	# funkce pro nacteni aliasu



### KONSTANTY ##################################################################

CONST_FILE_BUILDINGS = "buildings"	# soubor s aliasy budov
CONST_FILE_UNITS = "units"			# soubor s aliasy jednotek



### LOADBUILDINGS ##############################################################

def LoadBuildings():
	aliasBuildings = {}
	file = open(CONST_FILE_BUILDINGS, "r")
	cnt = 1
	while(1):
		line = file.readline()	# nacte radek
		if(line == ""): break	# konec souboru	
		aliasBuildings[cnt] = string.strip(line)	# oreze bile znaky na krajich
		cnt += 1
	file.close
	return aliasBuildings
	
	
	
### LOADUNITS ##################################################################

def LoadUnits():
	aliasUnits = {}
	file = open(CONST_FILE_UNITS, "r")
	cnt = 1
	while(1):
		line = file.readline()	# nacte radek
		if(line == ""): break	# konec souboru	
		aliasUnits[cnt] = string.strip(line)	# oreze bile znaky na krajich
		cnt += 1
	file.close
	return aliasUnits
	
