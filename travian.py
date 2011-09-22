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



"""
TODO: 
varovani o utocich a preplneni skladu sms a kdyz dojde zprava, farmareni, staveni budov, vojaku, upgradace, obchodovani, 
moznost uspani skriptu v config, davani explicitnich pozadavku do fronty, 
overit spravny nacteni zapor. hod. u surovin
monitorovat pohyb jednotek a staveni
moznost vypinani urc. fci - napr skript bude jen posilat sms pri utoku a nebude stavet
hrdina - samost promenna v dtb - uroven, zkusenosti, dovednosti, rasa...
rozlisit vsechny vojaky a vlastni vojaky a vojaky na ceste
osetreni prazdnych surovin. poli - aby se spravne nacitali
logy do ext. souboru i na stdout
prispusobit sleep casu dokonceni stavby
skript funguje az kdyz jsou vsechny pole aspon na lvl 1
u farmingu implementovat -1 jako vsechny vojaky co mam
udelat staveni budov a vojaku do fronty s podminkou do jakyho lvl
aktualizace poctu vojaku u farming a podpora -1, -2...
"""



### IMPORT #####################################################################

import socket		# sitove funkce
import random		# random
import time			# casove funkce
import string 		# retezce
import re			# regularni vyrazy
import smtplib		# smtp
import ConfigParser # ini

import parse	# parsovaci funkce pro ziskani dat z HTML
import alias	# funkce pro nacteni aliasu

# nacteni aliasu budov
aliasBuildings = alias.LoadBuildings();
aliasUnits = alias.LoadUnits();



### KONSTANTY ##################################################################

CONST_SERVER = "s4.travian.cz"
CONST_COOKIE = "Cookie: CAD=28775094%231248264785%230%230%23%230; T3E=%3DADM0EjOxkzN2QjN4QjMxoDMxoTOzAzY5UDO5ETO68mblBnOxEjNzIjOwMCMjETM2MjM; GP=file%3A%2F%2FC%3A%2FTravian%2F"
CONST_SERVER_ERR = 60	# doba cekani na dalsi pokus pripojeni pri selhani

CONST_MAIL_FROMADDR = "stud.fit.vutbr.cz"		# smtp server
CONST_MAIL_LOGIN = "xlogin00"					# login na mail
CONST_MAIL_PASSWD = "pass"						# heslo na mail
CONST_MAIL_TOADDR  = "user@vodafonemail.cz"		# mobilni email
CONST_MAIL_SMTP = "eva.fit.vutbr.cz"
CONST_MAIL_HEADER = "From: %s@%s\r\nTo: %s\r\n\r\n" % (CONST_MAIL_LOGIN, CONST_MAIL_FROMADDR, CONST_MAIL_TOADDR)

CONST_DICT_BUILD = "Ve výstavbě:"
CONST_DICT_BUSY = "Stavitelé mají momentálně hodně práce"
CONST_DICT_NORES = "Málo surovin"
CONST_DICT_FINISH = "Hotovo v"

CONST_FILE_CONFIG = "conf"
CONST_FILE_LOG = "log"
CONST_FILE_FARMING = "farming"

CONST_SLEEP_FARMING = 3

#CONF = {}
#LAST_FARMING = -1



### DEBUGFILE ##################################################################

def DebugFile(str, output):
	# DEBUG - ULOZENI STR DO SOUBORU
	file = open(output, "w")
	file.write(str)
	file.close



### SEND MAIL ##################################################################

def SendMail(msg):
    server = smtplib.SMTP(CONST_MAIL_SMTP, 587)
    #server.starttls()
    server.login(CONST_MAIL_LOGIN, CONST_MAIL_PASSWD)
    server.sendmail(CONST_MAIL_FROMADDR, CONST_MAIL_TOADDR, CONST_MAIL_HEADER + str("TRBOT3: ") + str(msg))
    server.quit()
    
    
    
### LOAD CONFIG ################################################################

def LoadConfig(file):
	config={}
	config = config.copy()
	cp = ConfigParser.ConfigParser()
	cp.read(file)
	for sec in cp.sections():
		name = string.lower(sec)
		for opt in cp.options(sec):
			config[name + "." + string.lower(opt)] = string.strip(cp.get(sec, opt))
	return config



### LOAD FARMING ###############################################################

def LoadFarming(file):
	farming = []
	file = open(file, "r")
	
	while(1):
		#zpracovani dat
		line = file.readline()
		if(line == ""): break
		
		# orezani bilych znaku
		line = string.strip(line)	
		
		# odstraneni komentaru
		index = string.find(line, "#")
		if(index != -1): line = line[:index]
		
		# parsovani
		attack = string.split(line,";")
		if(len(attack) != 14): continue
		
		farming.append(attack)
	
	file.close
	return farming
	

	
### LOG ########################################################################

def Log(str):
	# sms log
	global conf
	if(int(conf["mail.report"])): SendMail(str)
	
	str = time.strftime("%y/%m/%d %X ") + str
	
	# do souboru
	file = open(CONST_FILE_LOG, "a")
	file.write(str + "\n")
	file.close
	
	# na stdout
	print str



### SENDDATA ###################################################################

def SendData(request):
	# vytvoreni soketu
	#print "     DEBUG: komunikuji se serverem"
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	
	while True:
		try:
			s.connect((CONST_SERVER, 80))	# pripojeni soketu
			s.send(request)					# odeslani pozadavku

			# ziskani odpovedi
			recv = ""
			while True:
				buf = s.recv(65536)
				if(len(buf) > 0):
					recv += buf
				else:
					break

			s.close()	# uzavreni soketu
			break

		except:
			print "ERROR: Chyba pri komunikaci se serverem " + CONST_SERVER + ". Opakovani za " + str(CONST_SERVER_ERR) + " sekund."
			time.sleep(CONST_SERVER_ERR)
			continue

	return recv



### SETCOOKIE ##################################################################

def SetCookie(recv):
	global cookie		# globalni promenna cookie
	
	str = "Set-Cookie: "
	index = recv.find(str)
	
	# prenastaveni cookie z http hlavicky
	if index != -1:
		#print "     DEBUG: prenastavuju cookie"
		index += len(str)
		index2 = recv.find("=", index) + 1
		term = recv[index:index2]
		
		index3 = recv.find(";", index2)
		text = recv[index2:index3]
		
		index = cookie.find(term) + len(term)
		index2 = cookie.find(";", index)
		if index2 == -1:
			index2 = cookie.find("\r\n", index)

		cookie = cookie[:index] + text + cookie[index2:]



### LOGIN ######################################################################

def Login():
	global cookie		# globalni promenna cookie
		
	# HTTP pozadavek pro nacteni prihlasovaci stranky
	request = "GET / HTTP/1.1\r\n"
	request += "Host: " + CONST_SERVER + "\r\n"
	request += cookie + "\r\n\r\n"
	
	recv = SendData(request)			# zaslani pozadavku HTTP serveru
	SetCookie(recv)						# prenastaveni cookies
	
	### DEBUG FILE ###
	#DebugFile(recv, "!DEBUG_1.html")
	
	# vygenerovani retezce pro prihlasovaci udaje
	index = recv.find("\r\n\r\n") + 4
	index2 = recv.find('name="login"', index)
	index2 = recv.find('value="', index2) + len('value="')
	index3 = recv.find('"', index2)
	content = "w=1280%3A800&login=" + recv[index2: index3] + "&"
	index4 = recv.find('maxlength="15"', index)
	index2 = recv.rfind('name="', 0, index4) + len('name="')
	index3 = recv.find('"', index2)
	content += recv[index2: index3] + "="
	index2 = recv.rfind('value="', 0, index4) + len('value="')
	index3 = recv.find('"', index2)
	content += recv[index2: index3] + "&"
	index4 = recv.find('maxlength="20"', index)
	index2 = recv.rfind('name="', 0, index4) + len('name="')
	index3 = recv.find('"', index2)
	content += recv[index2: index3] + "="
	index2 = recv.rfind('value="', 0, index4) + len('value="')
	index3 = recv.find('"', index2)
	content += recv[index2: index3] + "&"
	index4 = recv.find('type="hidden"', index2)
	index2 = recv.find('name="', index4) + len('name="')
	index3 = recv.find('"', index2)
	content += recv[index2: index3] + "="
	index2 = recv.find('value="', index4) + len('value="')
	index3 = recv.find('"', index2)
	content += recv[index2: index3] + "&"
	content += "s1.x=" + str(random.randint(1,64)) + "&s1.y=" + str(random.randint(1,16)) + "&s1=login&autologin=ja"
	
	#print "     DEBUG: CONTENT: " + content
	# priklad content: "w=1280%3A800&login=1203630895&e559ad7=ROJI&eed4cb0=*******&e5967cc=dbcc0d9c43&s1.x=1&s1.y=1&s1=login&autologin=ja"

	# HTTP pozadavek pro prihlaseni do hry
	request = "POST /dorf1.php HTTP/1.1\r\n"
	request += "Host: " + CONST_SERVER + "\r\n"
	request += "Referer: http://" + CONST_SERVER + "/\r\n"
	request += cookie + "\r\n"
	request += "Content-Type: application/x-www-form-urlencoded\r\n"
	request += "Content-Length: " + str(len(content)) + "\r\n\r\n"
	request += content
	
	recv = SendData(request)			# zaslani pozadavku HTTP serveru
	SetCookie(recv)						# prenastaveni cookies
	
	# orezani hlavicky
	index = recv.find("\r\n\r\n")
	recv = recv[index+4:]
	
	return recv
	


### SENDREQUEST ################################################################

def SendRequest(file):
	global cookie		# globalni promenna cookie
	
	# HTTP pozadavek
	request = "GET " + file + " HTTP/1.1\r\n"
	request += "Host: " + CONST_SERVER + "\r\n"
	request += cookie + "\r\n\r\n"
	
	recv = SendData(request)			# zaslani pozadavku HTTP serveru
	SetCookie(recv)						# prenastaveni cookies
	
	# orezani hlavicky
	index = recv.find("\r\n\r\n")
	recv = recv[index+4:]
	
	return recv
	
	
	
### POSTREQUEST ################################################################

def PostRequest(file, content):
	global cookie		# globalni promenna cookie
	
	# HTTP pozadavek
	request = "POST " + file + " HTTP/1.1\r\n"
	request += "Host: " + CONST_SERVER + "\r\n"
	request += cookie + "\r\n"
	request += "Content-Type: application/x-www-form-urlencoded\r\n"
	request += "Content-Length: " + str(len(content)) + "\r\n\r\n"
	request += content
	
	recv = SendData(request)			# zaslani pozadavku HTTP serveru
	SetCookie(recv)						# prenastaveni cookies
	
	# orezani hlavicky
	index = recv.find("\r\n\r\n")
	recv = recv[index+4:]
	
	return recv
	
	
	
### DOFIELD ####################################################################

def DoField(field):
	#print "     DEBUG: DoField"
	
	# zjisteni nejmensiho levelu pole
	minimum = 1000
	for x in range(len(field)):
		level = field[x+1][1]
		if(level < minimum): minimum = level
			
	# zjisteni cetnosti poli s nejmensim levelem
	count = [0, 0, 0, 0]	# cetnost typu poli - wood, clay, iron, corn
	for x in range(len(field)):
		level = field[x+1][1]
		if(level == minimum):
			type = field[x+1][0]
			if(type == 1): count[0] += 1
			elif(type == 2): count[1] += 1
			elif(type == 3): count[2] += 1
			elif(type == 4): count[3] += 1
			
	# serazeni cetnosti, napr. [6,6,8,6] -> [8,6,6,6] -> [2,0,1,3]
	countSortIndex = [0, 0, 0, 0]
	countSort = count[:]
	countSort.sort()
	countSort.reverse()
	buf = count[:]
	for x in range(len(countSort)):
		countSortIndex[x] = buf.index(countSort[x])
		buf[countSortIndex[x]] = 1000
	#print "     DEBUG COUNT:", count, countSort, countSortIndex
	
	# pokus o postaveni typu pole s nejmensim levelem a co nejvetsi cetnosti
	# prochazi typy pole, zacina nejcetnejsim		
	for x in range(len(countSortIndex)):
		buildType = countSortIndex[x] + 1
		# pokud je cetnost vetsi jak 0
		if(count[countSortIndex[x]] > 0):
			for y in range(len(field)):
				# nalezeni konkretniho pole
				if(buildType == field[y+1][0] and minimum == field[y+1][1]):
					buildId = y+1
					# pokus o postaveni pole
					recv = SendRequest("/build.php?id=" + str(buildId))
					#print "     DEBUG POLE[typ,level,id]:", buildType, minimum, buildId
					if(recv.find(CONST_DICT_BUSY) != -1):
						#print "STAVITELE MAJI HODNE PRACE"
						break
					elif(recv.find(CONST_DICT_NORES) != -1):
						#print "NEDOSTATEK SUROVIN"
						break
					else:
						# zjisteni identifikatoru pro postaveni budovy
						tmp = re.compile("dorf1\.php\?a=.+?\">", re.DOTALL).findall(recv)
						try:
							c = re.compile(".+?c=|\">", re.DOTALL).sub("", tmp[0])
							recv = SendRequest("/dorf1.php?a=" + str(buildId) + "&c=" + str(c))	# postaveni pole
							
							Log("Stavim " + aliasBuildings[buildType] + " uroven " + str(minimum+1)) 
							return
						
						except:
							#print "POLE NELZE POSTAVIT"
							break

				
				
### DOFARMING ##################################################################

def DoFarming(farming, army, nation):
	#print "     DEBUG: DoFarming"
	
	# zjisteni narodnosti kvuli rozeznani vojaku dane rasy
	diff = 0
	if(nation == "Římané"): diff = 0
	elif(nation == "Germáni"): diff = 10
	elif(nation == "Galové"): diff = 20
	
	attack = 0 # priznak jestli za aktualni cyklus byli vyslani vojaci nebo ne
	last_farming = -1

	# prochazi farmy
	for x in range(len(farming)):
		noarmy = 0
		# kontrola stavu vojska
		for y in range(10):
			if(army[1+y+diff] < int(farming[x][3+y])):
				noarmy = 1
				break
		
		if(noarmy == 1): continue
		
		# id - shromazdiste=39; a - ? promenny; c - typ utoku, 4=loupez, 3=utok, 2=podpora; kid - id vesnice; t1 - falanga u21; t2 - sermir u22
		content = "id=39&a=" + str(x) + "&c=" + farming[x][0] + "&kid=" + farming[x][1] + "&t1=" + farming[x][3] + "&t2=" + farming[x][4] \
		+ "&t3=" + farming[x][5] + "&t4=" + farming[x][6] + "&t5=" + farming[x][7] + "&t6=" + farming[x][8] + "&t7=" \
		+ farming[x][9] + "&t8=" + farming[x][10] + "&t9=" + farming[x][11] + "&t10=" + farming[x][12] + "&t11=" \
		+ "0" + "&s1.x=37&s1.y=8&s1=ok"
		
		recv = PostRequest("/a2b.php", content)	# odesle prikaz na server
		
		soldiers = 0	# pocet vojaku
		for y in range(10):
			soldiers += int(farming[x][3+y])
			
		Log("Utocim s " + str(soldiers) + " vojaky na " + farming[x][2])
		
		# aktualizace army[]
		for y in range(10):
			army[1+y+diff] -= int(farming[x][3+y])
			
		attack = 1
		last_farming = x
	
		#print "     DEBUG ARMY:", army
		time.sleep(CONST_SLEEP_FARMING)
	
	# preusporadani farming[]
	if(attack):
		if(last_farming != len(farming)-1):
			farming = farming[last_farming+1:] + farming[:last_farming+1]
		
	#print "     DEBUG FARMING:", farming
	return farming
	
	
	
### DOWARNING ##################################################################

def DoWarning(attack, resources, resourcesMax):
	#print "     DEBUG: DoWarning"
	global conf
	
	resourcesWarn = 0
	attackWarn = 0
	
	# kontrola skladu
	for x in range(len(resources)-1):
		if(resources[x] + int(conf["do.resources_diff"]) >= resourcesMax[x]):
			resourcesWarn = 1
			break
			
	# kontrola utoku
	if(len(attack) > 0):
		attackWarn = 1
		
	# odeslani upozorneni
	if(attackWarn == 1 or resourcesWarn == 1):
		msg = ""
		if(attackWarn): msg += attack[0] + " utok za " + attack[1] + "! "
		if(resourcesWarn): 
			msg += "Sklady: " + str(resources[0]) + "/" + str(resourcesMax[0]) + " " \
			+ str(resources[1]) + "/" + str(resourcesMax[1]) + " " \
			+ str(resources[2]) + "/" + str(resourcesMax[2]) + " " \
			+ str(resources[3]) + "/" + str(resourcesMax[3])

		SendMail(msg)
		


### TRAV #######################################################################

def Trav():
	farming = []			# farmy - nacte se jen jednou pri spusteni
	farming = LoadFarming(CONST_FILE_FARMING)
	
	while(1):	
		# databaze	
		# obecna data
		rank = 0			# umisteni ve hre
		population = 0		# celkova populace
		uid = ""			# id hrace
		aid = ""			# id aliance
		player = ""			# hrac
		nation = ""			# rasa
		aliance = ""		# aliance
		village = []		# seznam vesnic - nazev, populace, poloha
		
		# vesnice
		resources = []		# zasoby - wood, clay, iron, corn, usage
		resourcesMax = []	# zasoby maximum - wood, clay, iron, corn, usage
		resourcesProd = []	# zasoby produkce - wood, clay, iron, corn
		field = {}			# pole - typ, level
		building = {}		# budova - typ, level
		army = {}			# vojaci
		attack = []			# utok - pocet utoku, hrac, cas
		defence = []		# podpora - pocet utoku, hrac, cas
	
		# conf
		global conf
		conf = LoadConfig(CONST_FILE_CONFIG)
		#print "     DEBUG CONF:", conf
		#print "     DEBUG FARMING:", farming
		
		
		
		# uspani celeho skriptu
		if(not int(conf["sleep.sleep"])):
		
			# inicializace
			global cookie				# globalni promenna
			cookie = CONST_COOKIE		# inicializace cookies
			recv = Login()				# zalogovani do hry
			### DEBUG FILE ###
			#DebugFile(recv, "!DEBUG_2.html")
			
			# zpracovani souboru dorf1
			uid, resources, resourcesMax, resourcesProd, field, army, attack, defence = parse.ParseDorf1(recv)
		
			# zpracovani souboru dorf2
			recv = SendRequest("/dorf2.php")
			### DEBUG FILE ###
			#DebugFile(recv, "!DEBUG_3.html")
			building = parse.ParseDorf2(recv)
		
			# zpracovani souboru spieler
			recv = SendRequest("/spieler.php?uid=" + str(uid))
			### DEBUG FILE ###
			#DebugFile(recv, "!DEBUG_4.html")
			rank, population, player, nation, aliance, aid, village = parse.ParseSpieler(recv)
		
		
		
			# kontrolni vypis databaze
			#"""
			print "     DEBUG DTB: uid:", uid
			print "     DEBUG DTB: aid:", aid
			print "     DEBUG DTB: rank:", rank
			print "     DEBUG DTB: population:", population
			print "     DEBUG DTB: player:", player
			print "     DEBUG DTB: nation:", nation
			print "     DEBUG DTB: aliance:", aliance
			print "     DEBUG DTB: village:", village
			
			print "     DEBUG DTB: resources:", resources
			print "     DEBUG DTB: resourcesMax:", resourcesMax
			print "     DEBUG DTB: resourcesProd:", resourcesProd
			print "     DEBUG DTB: field:", field
			print "     DEBUG DTB: building:", building
			print "     DEBUG DTB: army:", army
			print "     DEBUG DTB: attack:", attack
			print "     DEBUG DTB: defence:", defence
			#"""
		
		
			# funkce
			if(int(conf["do.field"])): DoField(field)
			if(int(conf["do.farming"])): farming = DoFarming(farming, army, nation)
			if(int(conf["do.warning"])): DoWarning(attack, resources, resourcesMax)
		
			
			# logout
			delay = 60 * (int(conf["sleep.logout"]) + random.randint(0,int(conf["sleep.diff"])))
			#print "     DEBUG LOGOUT SLEEP:", delay
			time.sleep(delay)	# uspani skriptu v sec
			recv = SendRequest("/logout.php")
			### DEBUG FILE ###
			#DebugFile(recv, "!DEBUG_5.html")
		
		
		
		# uspani skriptu
		hour = time.strftime("%H")
		# noc
		if(hour >= int(conf["sleep.night_start"]) and hour < int(conf["sleep.night_end"])):
			delay = 60 * (int(conf["sleep.night"]) + random.randint(0,int(conf["sleep.diff"])))
		# den
		else:
			delay = 60 * (int(conf["sleep.day"]) + random.randint(0,int(conf["sleep.diff"])))
		#print "     DEBUG SCRIPT SLEEP:", delay
		time.sleep(delay)	# uspani skriptu v sec
	


### MAIN #######################################################################

if (__name__=="__main__"):
	try:
		Trav()
	except:
		global conf
		if(int(conf["mail.exception"])): SendMail("Doslo k vyjimce!")
		raise

