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
import re		# regularni vyrazy

import alias	# funkce pro nacteni aliasu



### KONSTANTY ##################################################################

CONST_DICT_LEVEL = "úroveň"				# slovo úroveň
CONST_DICT_PLAYER = "Hráč "				# slovo Hráč
CONST_DICT_RANK = "Místo:"				# slovo Místo:
CONST_DICT_POPULATION = "Populace:"		# slovo Populace:
CONST_DICT_NATION = "Národ:"			# slovo Národ:
CONST_DICT_ALIANCE = "Aliance:"			# slovo Aliance:
CONST_DICT_MAIN = "Hlavní vesnice"		# slovo Hlavní vesnice
CONST_DICT_CORN_USAGE = "Spotřeba obilí"

# nacteni aliasu budov
aliasBuildings = alias.LoadBuildings();
aliasUnits = alias.LoadUnits();



### PARSEDORF1 #################################################################

def ParseDorf1(recv):
	#print "     DEBUG: ParseDorf1"
	
	"""
	### DEGUG SIMULACE ###
	print "     DEBUG: Simuluji externi soubor"
	recv = ""
	file = open("TEST/HL_dorf1.html", "r")
	while(1):
		line = file.readline()
		if(line == ""): break
		else: recv += line
	file.close
	"""
	
	# databaze
	uid = ""			# id hrace
	resources = []		# zasoby - wood, clay, iron, corn, usage
	resourcesMax = []	# zasoby maximum - wood, clay, iron, corn, usage
	resourcesProd = []	# zasoby produkce - wood, clay, iron, corn
	field = {}			# budova - id, typ, level
	army = {}			# vojaci
	attack = []			# utok - pocet utoku, cas
	defence = []		# podpora - pocet utoku, cas
	
	
	# uid
	tmp = re.compile("spieler\.php\?uid=\d+", re.DOTALL).findall(recv)
	uid = re.compile("spieler\.php\?uid=", re.DOTALL).sub("", tmp[0])
	

	# resourcesProd, resources, resourcesMax - wood, clay, iron, corn
	list = re.compile("\d+\">\d+/\d+", re.DOTALL).findall(recv)
	for x in range(len(list)):
		prod = re.compile("\">.+", re.DOTALL).sub("", list[x])
		res = re.compile("\d+\">|/\d+", re.DOTALL).sub("", list[x])
		max = re.compile(".+/", re.DOTALL).sub("", list[x])
		resourcesProd.append(int(prod))
		resources.append(int(res))
		resourcesMax.append(int(max))

	
	# resources, resourcesMax - usage
	index = recv.find(CONST_DICT_CORN_USAGE)
	crop = recv[index:]
	tmp = re.compile("\d+/\d+", re.DOTALL).findall(crop)
	res = re.compile("/\d+", re.DOTALL).sub("", tmp[0])
	maxim = re.compile("\d+/", re.DOTALL).sub("", tmp[0])
	resources.append(int(res))
	resourcesMax.append(int(maxim))

	
	# field
	index = recv.find("village_map")
	crop = recv[index:]
	list = re.compile('"[^"()]+' + CONST_DICT_LEVEL + '[^"()]+"', re.DOTALL).findall(crop)
	for x in range(len(list)):
		lvl = re.compile("[^\d]+", re.DOTALL).sub("", list[x])
		for y in range(len(aliasBuildings)):
			if(list[x].find(aliasBuildings[y+1]) != -1):
				type = y+1
		field[x+1] = [type, int(lvl)]

	
	# army
	for x in range(30): army[x+1] = 0 # prazdna army
	list = re.compile("unit u\d+.*?>\d+<", re.DOTALL).findall(recv)
	for x in range(len(list)):
		if(list[x].find("hero") != -1):
			id = 0
			cnt = 1
		else:
			id = re.compile("unit u\d+", re.DOTALL).findall(list[x])
			id = int(id[0][6:])
			cnt = re.compile(">\d+?<", re.DOTALL).findall(list[x])
			cnt = int(cnt[0][1:-1])
		army[id] = cnt
		
		
	# attack
	list = re.compile("a1.+?\d+:\d+:\d+", re.DOTALL).findall(recv)
	for x in range(len(list)):
		count = re.compile(">\d+&", re.DOTALL).findall(list[x])
		count = count[0][1:-1]
		time = re.compile("\d+:\d+:\d+", re.DOTALL).findall(list[x])
		time = time[0]
		attack.append(count)
		attack.append(time)
	

	return uid, resources, resourcesMax, resourcesProd, field, army, attack, defence



### PARSEDORF2 #################################################################

def ParseDorf2(recv):
	#print "     DEBUG: ParseDorf2"
	
	"""
	### DEGUG SIMULACE ###
	print "     DEBUG: Simuluji externi soubor"
	recv = ""
	file = open("TEST/HL_dorf2.html", "r")
	while(1):
		line = file.readline()
		if(line == ""): break
		else: recv += line
	file.close
	"""
	
	# databaze
	building = {}		# budova - typ, level
	
	
	# building
	index = recv.find("village_map")
	crop = recv[index:]
	list = re.compile('\d+[^\d]+"[^"()]+' + CONST_DICT_LEVEL + '[^"()]+"', re.DOTALL).findall(crop)
	for x in range(len(list)):
		id = re.compile("[^\d]+.+", re.DOTALL).sub("", list[x])
		lvl = re.compile("^\d+|[^\d]+", re.DOTALL).sub("", list[x])
		for y in range(len(aliasBuildings)):
			if(list[x].find(aliasBuildings[y+1]) != -1):
				type = y+1
		building[int(id)] = [type, int(lvl)]
		
	
	return building



### PARSESPIELER ###############################################################

def ParseSpieler(recv):
	#print "     DEBUG: ParseSpieler"
	
	"""
	### DEGUG SIMULACE ###
	print "     DEBUG: Simuluji externi soubor"
	recv = ""
	file = open("TEST/HL_spieler.html", "r")
	while(1):
		line = file.readline()
		if(line == ""): break
		else: recv += line
	file.close
	"""
	
	# databaze
	rank = 0			# umisteni ve hre
	population = 0		# celkova populace
	player = ""			# hrac
	nation = ""			# rasa
	aliance = ""		# aliance
	aid = ""			# id aliance
	village = []		# seznam vesnic - nazev, id, populace, poloha x, poloha y
	
	
	# rank
	tmp = re.compile(CONST_DICT_RANK + ".+?\d+?<\/td>", re.DOTALL).findall(recv)
	rank = re.compile("\".*\"", re.DOTALL).sub("", tmp[0])
	rank = re.compile("[^\d]+", re.DOTALL).sub("", rank)
	rank = int(rank)
	
	
	# population
	tmp = re.compile(CONST_DICT_POPULATION + ".+?\d+?<\/td>", re.DOTALL).findall(recv)
	population = re.compile("\".*\"", re.DOTALL).sub("", tmp[0])
	population = re.compile("[^\d]+", re.DOTALL).sub("", population)
	population = int(population)
	
	
	# player
	tmp = re.compile(CONST_DICT_PLAYER + ".+?<", re.DOTALL).findall(recv)
	player = re.compile(CONST_DICT_PLAYER + "|<", re.DOTALL).sub("", tmp[0])
	
	
	# nation
	tmp = re.compile(CONST_DICT_NATION + ".+?<\/td>", re.DOTALL).findall(recv)
	nation = re.compile(CONST_DICT_NATION + ".+?<td>|<\/td>", re.DOTALL).sub("", tmp[0])
	

	# aliance
	tmp = re.compile(CONST_DICT_ALIANCE + ".+<\/tr>", re.DOTALL).findall(recv)
	aliance = re.compile(CONST_DICT_ALIANCE + ".+?<td>|<\/td>.+|<a.+?>|<\/a>", re.DOTALL).sub("", tmp[0])

	
	# aid
	tmp = re.compile("allianz\.php\?aid=\d+", re.DOTALL).findall(recv)
	if(len(tmp)>0):
		aid = re.compile("allianz\.php\?aid=", re.DOTALL).sub("", tmp[0])
	
	
	# village
	list = re.compile("karte\.php\?d=.+?<\/tr>", re.DOTALL).findall(recv)
	for x in range(len(list)):
		villName = re.compile("karte.+?>|<\/a>.+", re.DOTALL).sub("", list[x])	
		tmp = re.compile("\(\d+", re.DOTALL).findall(list[x])
		villX = tmp[0][1:]
		tmp = re.compile("\d+\)", re.DOTALL).findall(list[x])
		villY = tmp[0][:-1]
		tmp = re.compile("<td.+>\d+<\/td>", re.DOTALL).findall(list[x])
		villPopulation = re.compile("<td.+?>|<\/td>", re.DOTALL).sub("", tmp[0])
		if(list[x].find(CONST_DICT_MAIN) != -1):
			village.insert(0, [villName, "", villPopulation, villX, villY])
		else:
			village.append([villName, "", villPopulation, villX, villY])
	
	
	# village id
	"""	
	list = re.compile("\?newdid.+?<\/a>", re.DOTALL).findall(recv)
	for x in range(len(list)):
		villName = re.compile("\?newdid.+?\>|<\/a>", re.DOTALL).sub("", list[x])
		id = re.compile('\?newdid=|&uid.+', re.DOTALL).sub("", list[x])
		for y in range(len(village)):
			if(village[y][0] == villName):
				village[y][1] = id
				break
	"""

	return rank, population, player, nation, aliance, aid, village
	
