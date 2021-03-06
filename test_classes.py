try:
	import simplejson as json
except:
	print("'simplejson' package not installed, defaulting to json (slower) instead")
	import json
import time
import sqlite3
import urllib.request
import random
SERVICEURL = 'http://pokeapi.co/api/v2/'

conn = sqlite3.connect('cache.db')
cur = conn.cursor()
'''cur.executescript(''
CREATE TABLE IF NOT EXISTS BasePokemon (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	name TEXT,
	type1 TEXT,
	type2 TEXT,
	baseHP INTEGER NOT NULL,
	baseATT INTEGER NOT NULL,
	baseDEF INTEGER NOT NULL,
	baseSPATT INTEGER NOT NULL,
	baseSPDEF INTEGER NOT NULL,
	baseSPD INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS Moves (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	name TEXT,
	type TEXT,
	basePower INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS Pokemon (
	pokemon_id INTEGER,
	move1_id INTEGER,
	move2_id INTEGER,
	move3_id INTEGER,
	move4_id INTEGER,
	PRIMARY KEY(pokemon_id, move1_id, move2_id, move3_id, move4_id)
)
'')'''
		
class GameManager:
	def __init__(self):
		self.gameturn = 0 #TEMPORARY, actual game does not have such feature
		self.gameover = False
		
		while True:
			trainername = input('Trainer Name: ') #For flavor purposes only
			if trainername.strip() != '':
				break
			else:
				print('Not a valid trainer name, try again')
				
		self._player = Trainer(trainername, Trainer.PLAYER)
		self._opponent = Trainer('Computer', Trainer.OPPONENT)
		#Initial text mirroring the actual game
		print('You are challenged by {}!'.format(self._opponent.name))
		print('Go! {}!'.format(self._player.getCurPkmn().name))
		print('{} sent out {}!'.format(self._opponent.name, self._opponent.getCurPkmn().name))
		
	def play(self):
		while self.gameover == False:
			self.turn()
	
	def display(self): #Fancy formatting mirroring the actual game
		player_pkmn = self._player.getCurPkmn()
		player_pkmn_num_bars = int(player_pkmn.stats[Pokemon.HP] / player_pkmn.maxHP * 8)
		opponent_pkmn = self._opponent.getCurPkmn()
		opponent_pkmn_num_bars = int(opponent_pkmn.stats[Pokemon.HP] / opponent_pkmn.maxHP * 8)
		print('---------------------------------------')
		print('TURN #{}'.format(self.gameturn))
		print('\t\t\t{}  Lv. {}'.format(opponent_pkmn.name, opponent_pkmn.level))
		print('\t\t\tHP: [{}]'.format("".join(opponent_pkmn_num_bars * ['\\'] + (8 - opponent_pkmn_num_bars) * [' '])))
		print()
		print('{} Lv. {}'.format(player_pkmn.name, player_pkmn.level))
		print('HP: {}/{}'.format(player_pkmn.stats[Pokemon.HP], player_pkmn.maxHP))
	
	def _order(self, player_pkmn_move, opponent_pkmn_move):
		player_pkmn, opponent_pkmn = self._player.getCurPkmn(), self._opponent.getCurPkmn()
		if player_pkmn_move != None and opponent_pkmn_move != None:
			if player_pkmn_move.priority > opponent_pkmn_move.priority:
				return Trainer.PLAYER
			elif player_pkmn_move.priority < opponent_pkmn_move.priority:
				return Trainer.OPPONENT
		elif player_pkmn_move == None and opponent_pkmn_move != None: #Player switches
			return Trainer.PLAYER
		elif player_pkmn_move != None and opponent_pkmn_move == None: #Opponent switches
			return Trainer.OPPONENT
		
		if player_pkmn.calcStat(Pokemon.SPD) > opponent_pkmn.calcStat(Pokemon.SPD):
			return Trainer.PLAYER
		elif player_pkmn.calcStat(Pokemon.SPD) < opponent_pkmn.calcStat(Pokemon.SPD):
			return Trainer.OPPONENT
		else:
			return random.choice([Trainer.PLAYER, Trainer.OPPONENT]) #Speed Tie, ordering is randomly determined
	
	#def _target(self.)
	def execMove(self, user_pkmn, user_move, receiver_pkmn):
		user = user_pkmn.getTrainer()
		receiver = receiver_pkmn.getTrainer()
		
		if user_move == None:
			user.switch()
			return 1
		
		attackmsg = '{} used {}!'.format(user_pkmn.name, user_move.name)
		if user.type == Trainer.OPPONENT:
			attackmsg = 'The opposing {}'.format(attackmsg)
		print(attackmsg)
		
		target = user_move.getTarget()
		if target == Move.ALLY or target == Move.ALL or target == Move.OTHER:
			print('But it failed!')
			return 1
		
		if user_move.hasStatChange() and user_move.damage_class == "Status":
			if target == Move.PLAYER:
				user_pkmn.changeAllStats(user_move.stat_boosts)
				#print(user_pkmn.getAllStatBoost())
			else:
				receiver_pkmn.changeAllStats(user_move.stat_boosts)
				#print(receiver_pkmn.getAllStatBoost())
				
		if user_move.power > 0 and user_pkmn.inflictdmg(user_move, receiver_pkmn) == True: #does move do damage?
			if not receiver_pkmn.isAlive(): #does move faint pokemon?
				faintmsg = '{} fainted!'.format(receiver_pkmn.name)
				if receiver.type == Trainer.OPPONENT:
					faintmsg = 'The opposing {}'.format(faintmsg)
				print(faintmsg)
				receiver.sendNewPkmn()
				if receiver.getNumPkmn() == 0:
					if receiver.type == Trainer.OPPONENT:
						print('You defeated {}!'.format(receiver.name))
					else:
						print('You lost to {}!'.format(user.name))
					self.gameover = True
				else:
					print('{} sent out {}!'.format(receiver.name, receiver.getCurPkmn().name))
				return 0 #Turn ends
			elif user_move.hasStatChange() and random.randint(1, 100) <= user_move.effect_chance: #non-status move
				#print('effect goes here')
				if target == Move.PLAYER:
					user_pkmn.changeAllStats(user_move.stat_boosts)
					#print(user_pkmn.getAllStatBoost())
				else:
					receiver_pkmn.changeAllStats(user_move.stat_boosts)
					#print(receiver_pkmn.getAllStatBoost())
		return 1 #Turn continues
	
	def turn(self):
		self.gameturn += 1
		self.display()
		player_pkmn_move, opponent_pkmn_move = self._player.getMove(), self._opponent.getMove()
		order = self._order(player_pkmn_move, opponent_pkmn_move) #Either 0 or 1
		if order == Trainer.PLAYER:
			if self.execMove(self._player.getCurPkmn(), player_pkmn_move, self._opponent.getCurPkmn()) == 1:
				self.execMove(self._opponent.getCurPkmn(), opponent_pkmn_move, self._player.getCurPkmn())
		else:
			if self.execMove(self._opponent.getCurPkmn(), opponent_pkmn_move, self._player.getCurPkmn()) == 1:
				self.execMove(self._player.getCurPkmn(), player_pkmn_move, self._opponent.getCurPkmn())
				
		#end of turn events
		
class Trainer:
	NUM_PKMN = 6
	PLAYER = 0
	OPPONENT = 1
	
	def __init__(self, name, player):
		self.name = name
		self.type = player
		self._trainer_pkmn = list()
		if self.type == Trainer.PLAYER:
			for num in range(Trainer.NUM_PKMN):
				while True:
					pkmnname = input('Pokemon #{}: '.format(num + 1)).strip()
					if pkmnname == '':
						cur.execute('''
						SELECT COUNT(*) FROM BasePokemon
						''')
						if cur.fetchone()[0] > 0:
							cur.execute('''
							SELECT name FROM BasePokemon
							ORDER BY RANDOM()
							LIMIT 1
							''')
							pkmnname = cur.fetchone()[0]
							print('No input, selecting random Pokemon: {}'.format(pkmnname))
							break;
						else:
							print('Not a valid Pokemon name, try again')
					elif not pkmnname.isdigit():
						cur.execute('''
						SELECT * FROM BasePokemon WHERE name = ?
						''', (pkmnname.capitalize(), ))
						if cur.fetchone() != None:	
							break
						req = urllib.request.Request(
							'{}pokemon/{}/'.format(SERVICEURL, pkmnname.lower()),
							data=None,
							headers={
								'User-Agent': 'Chrome/54.0.2840.71'
							}
						)
						
						try:
							contents = urllib.request.urlopen(req).read().decode('utf-8')
						except:
							print('Not a valid Pokemon name, try again')
							continue
							
						js = json.loads(str(contents))
						stats = js['stats']
						types = js['types']
						if len(types) == 2: #Dual typing
							type1 = types[1]['type']['name'].capitalize()
							type2 = types[0]['type']['name'].capitalize()
						else:
							type1 = types[0]['type']['name'].capitalize()
							type2 = None
							
						cur.execute('''
						INSERT INTO BasePokemon(name, type1, type2, baseHP, baseATT, baseDEF, baseSPATT, baseSPDEF, baseSPD) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
						''', (pkmnname.capitalize(), type1, type2, stats[5]['base_stat'], stats[4]['base_stat'], stats[3]['base_stat'], stats[2]['base_stat'], stats[1]['base_stat'], stats[0]['base_stat']))
						break
					print('Not a valid Pokemon name, try again')
				
				self._trainer_pkmn.append(Pokemon(pkmnname.capitalize(), self))
			conn.commit()
		else:
			for num in range(Trainer.NUM_PKMN):
				cur.execute('''
				SELECT name FROM BasePokemon
				ORDER BY RANDOM()
				LIMIT 1
				''')
				self._trainer_pkmn.append(Pokemon(cur.fetchone()[0], self))
				
		self.cur_pkmn_index = 0
		self.switch_pkmn_index = -1
	
	def getCurPkmn(self):
		return self._trainer_pkmn[self.cur_pkmn_index]
		
	def getNumPkmn(self):
		return Trainer.NUM_PKMN - self.cur_pkmn_index
		
	def sendNewPkmn(self):
		self.cur_pkmn_index += 1
		
	def showPkmn(self):
		COLS = 2
		print('\n'.join(['{0.name} Lv. {0.level}\t\t{1.name} Lv. {1.level}'.format(*pair) for pair in [self._trainer_pkmn[i:i + COLS] for i in range(0, len(self._trainer_pkmn), COLS)]]))
		#for pkmn in self._trainer_pkmn:
			#print('{name} Lv. {lv}\n{type}\n{curHP}/{maxHP}'.format(name=pkmn.name, lv=pkmn.level, type='/'.join([x for x in pkmn.type if x != None]), curHP=pkmn.stats[Pokemon.HP], maxHP=pkmn.maxHP))
		#print()
	
	def switch(self):
		assert(self.switch_pkmn_index >= 1 and self.switch_pkmn_index <= 5)
		print('{trainer} withdrew {name}!'.format(trainer=self.name, name=self.getCurPkmn().name))
		self._trainer_pkmn[self.cur_pkmn_index], self._trainer_pkmn[self.switch_pkmn_index] = self._trainer_pkmn[self.switch_pkmn_index], self._trainer_pkmn[self.cur_pkmn_index]
		print('{trainer} sent out {name}!'.format(trainer=self.name, name=self.getCurPkmn().name))
	
	def getMove(self): #Returns index of move
		pkmn = self.getCurPkmn()
		if self.type == Trainer.OPPONENT:
			return random.choice(pkmn.moves) # Randomly get a move
		
		showparty = False
		while True:
			if showparty == False:
				movenum = input('What will {} do?\n{}(1) {}(2) {}(3) {}(4) Party(p): '.format(pkmn.name, *(o.name for o in pkmn.moves)))
				print()
				if movenum.isdigit() and int(movenum) >= 1 and int(movenum) <= 4:
					return pkmn.moves[int(movenum) - 1] # Number (not index) of the move to use
				elif movenum == 'p':
					self.showPkmn()
					showparty = True
				else:
					print("Oak's words echoed... There's a time and place for everything but not now!")
			else:
				pkmnchoice = input('Pokemon to switch to (1 - 6, press b to go back): ')
				print()
				if pkmnchoice.isdigit() and int(pkmnchoice) >= 1 and int(pkmnchoice) <= 6:
					pkmnchoice = int(pkmnchoice)
					if pkmnchoice == 1:
						print('That Pokemon is already in battle!')
					elif self._trainer_pkmn[pkmnchoice - 1].stats[Pokemon.HP] <= 0:
						print('That Pokemon is too weak to fight!')
					else:
						self.switch_pkmn_index = pkmnchoice - 1
						return None # Switches take up a move but are not actually one
				elif pkmnchoice == 'b':
					showparty = False
				else:
					print("Oak's words echoed... There's a time and place for everything but not now!")
		
class Pokemon:
	NUM_MOVES = 4
	NUM_STATS = 6
	MAX_LEVEL = 100
	HP = 0
	ATT = 1
	DEF = 2
	SPATT = 3
	SPDEF = 4
	SPD = 5
	TRANSLATION = { HP: 'HP',
					ATT: 'attack',
					DEF: 'defense',
					SPATT: 'special attack',
					SPDEF: 'special defense',
					SPD: 'speed' }
	
	def __init__(self, name, trainer):
		self.trainer = trainer
		self.name = name
		cur.execute('''
		SELECT move.formatted_name FROM BasePokemon as pkmn JOIN MovesManager JOIN Moves as move
		ON pkmn.id = MovesManager.pokemon_id AND MovesManager.move_id = move.id
		WHERE pkmn.name = ?
		ORDER BY RANDOM()
		LIMIT 4
		''', (name, ))
		self.moves = [Move(movename[0]) for movename in cur.fetchall()]
		self.level = 50
		cur.execute('''
		SELECT type1, type2, baseHP, baseATT, baseDEF, baseSPATT, baseSPDEF, baseSPD FROM BasePokemon WHERE name = ?
		''', (name, ))
		queryresults = cur.fetchone()
		self.type = (queryresults[0], queryresults[1])
		self.stats = [(base_stat * 2 + 31) * self.level // 100 + 5 for base_stat in queryresults[2:] ]
		self.stats[Pokemon.HP] += self.level + 5
		self.maxHP = self.stats[Pokemon.HP]
		self.statboosts = 0x66666
	
	def getTrainer(self):
		return self.trainer
		
	def isAlive(self):
		return self.stats[Pokemon.HP] > 0
	
	def inflictdmg(self, move, pkmn):
		if move.damage_class == "Physical":
			attstat = Pokemon.ATT
			defstat = Pokemon.DEF
		elif move.damage_class == "Special": #if move is special, use the special att and special def stats to calculate dmg
			attstat = Pokemon.SPATT
			defstat = Pokemon.SPDEF
		else: #Status move
			return False
		
		if move.accuracy != -1 and random.randint(1, 100) > move.accuracy:
			print('The attack missed!')
			return False
			
		critical = random.random() < 0.0625 #Critical hit or no, 6.25% for critical hit
		if critical == True: #Critical hits ignore stat changes
			attacking_stat = self.stats[attstat]
			defending_stat = self.stats[defstat]
		else:
			attacking_stat = self.calcStat(attstat)
			defending_stat = self.calcStat(defstat)
		
		#damage formula, not accounting for STAB and type and the weird small modifiers
		dmg = (((2 * self.level + 10) / 250) * (attacking_stat / defending_stat) * move.power + 2) * random.uniform(0.85, 1)
		
		if self.type[0] == move.type or (self.type[1] != None and self.type[1] == move.type):
			dmg *= 1.5 #Same Type Attack Bonus (STAB)
		
		type_multiplier = 1
		for type in pkmn.type:
			if type != None and type in Move.typechart[move.type]:
				type_multiplier *= Move.typechart[move.type][type]
		
		if type_multiplier == 0:
			print('It has no effect...')
		elif type_multiplier > 1:
			print('It\'s super effective!')
		elif type_multiplier < 1:
			print('It\'s not very effective...')
		dmg *= type_multiplier
		
		if random.random() < 0.0625 and type_multiplier > 0:
			print('A critical hit!')
			dmg *= 1.5 #specific to generation VI
		
		pkmn.takedmg(int(dmg))
		return int(dmg) != 0
	
	def takedmg(self, amt):
		self.stats[Pokemon.HP] = max(0, self.stats[Pokemon.HP] - amt)
		return self.isAlive()
		
	def calcStat(self, stat):
		assert(stat >= 1 and stat <= 5)
		statboost = self.getStatBoost(stat)
		statmultiplier = abs(statboost) / 2 + 1
		if statboost < 0:
			statmultiplier = 1 / statmultiplier
		return self.stats[stat] * statmultiplier
		
	def getStatBoost(self, stat): #Stage of a particular stat
		assert(stat >= 1 and stat <= 5) # ATT -> 1, DEF -> 2, ..., SPD -> 5
		return (self.statboosts >> 4 * (5 - stat) & 0xF) - 6
	
	def getAllStatBoost(self):
		return [ int(stat, 16) for stat in hex(self.statboosts)[2:] ]
	
	def changeAllStats(self, statboosts):
		assert(statboosts >= 0 and statboosts <= 0xCCCCC)
		
		stat = 4
		while stat >= 0:
			statboost = ((statboosts >> stat * 4)& 0xF) - 6
			if statboost != 0:
				self.increaseStatStage(5 - stat, statboost) #5 is the length of our statboosts
			stat -= 1
		return self.statboosts
		
	def increaseStatStage(self, stat, stage):
		assert(stat >= 1 and stat <= 5)
		
		if self.trainer.type == Trainer.PLAYER:
			text = ""
		else:
			text = "The opposing "
			
		currentStat = self.getStatBoost(stat)
		if stage > 0:
			change = min(6, currentStat + stage) - currentStat
			if change == 0:
				print("{}{}'s {} won't go any higher!".format(text, self.name, Pokemon.TRANSLATION[stat]))
			elif change == 1:
				print("{}{}'s {} rose!".format(text, self.name, Pokemon.TRANSLATION[stat]))
			elif change == 2:
				print("{}{}'s {} rose sharply!".format(text, self.name, Pokemon.TRANSLATION[stat]))
			elif change == 3:
				print("{}{}'s {} rose drastically!".format(text, self.name, Pokemon.TRANSLATION[stat]))
			else:
				print("THis is belly drum")
		else:
			change = max(-6, currentStat + stage) - currentStat
			if change == 0:
				print("{}{}'s {} won't go any lower!".format(text, self.name, Pokemon.TRANSLATION[stat]))
			elif change == -1:
				print("{}{}'s {} fell!".format(text, self.name, Pokemon.TRANSLATION[stat]))
			elif change == -2:
				print("{}{}'s {} harshly fell!".format(text, self.name, Pokemon.TRANSLATION[stat]))
			elif change == -3:
				print("{}{}'s {} severely fell!".format(text, self.name, Pokemon.TRANSLATION[stat]))
			else:
				print("THis is momento") 
		self.statboosts = self.statboosts & ~(0xF << 4 * (5 - stat)) | ((currentStat + 6 + change) << 4 * (5 - stat))
		return self.statboosts

class Move:
	# Type matchup chart
	PLAYER = 0
	OPPONENT = 1
	ALLY = 2
	ALL = 3
	OTHER = 4
	
	typechart = {'Normal': {'Rock': 0.5, 'Ghost': 0, 'Steel': 0.5},
				'Fire': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 2, 'Bug': 2, 'Rock': 0.5, 'Dragon': 0.5, 'Steel': 2},
				'Water': {'Fire': 2, 'Water': 0.5, 'Grass': 0.5, 'Ground': 2, 'Rock': 2, 'Dragon': 0.5},
				'Electric': {'Water': 2, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0, 'Flying': 2, 'Dragon': 0.5},
				'Grass': {'Fire': 0.5, 'Water': 2, 'Grass': 0.5, 'Poison': 0.5, 'Ground': 2, 'Flying': 0.5, 'Bug': 0.5, 'Rock': 2, 'Dragon': 0.5, 'Steel': 0.5},
				'Ice': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 0.5, 'Ground': 2, 'Flying': 2, 'Dragon': 2, 'Steel': 0.5},
				'Fighting': {'Normal': 2, 'Ice': 2, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Rock': 2, 'Ghost': 0, 'Dark': 2, 'Steel': 2, 'Fairy': 0.5},
				'Poison': {'Grass': 2, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0, 'Fairy': 2},
				'Ground': {'Fire': 2, 'Electric': 2, 'Grass': 0.5, 'Poison': 2, 'Flying': 0, 'Bug': 0.5, 'Rock': 2, 'Steel': 2},
				'Flying': {'Electric': 0.5, 'Grass': 2, 'Fighting': 2, 'Bug': 2, 'Rock': 0.5, 'Steel': 0.5},
				'Psychic': {'Fighting': 2, 'Poison': 2, 'Psychic': 0.5, 'Dark': 0, 'Steel': 0.5},
				'Bug': {'Fire': 0.5, 'Grass': 2, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 2, 'Ghost': 0.5, 'Dark': 2, 'Steel': 0.5, 'Fairy': 0.5},
				'Rock': {'Fire': 2, 'Ice': 2, 'Fighting': 0.5, 'Ground': 0.5, 'Flying': 2, 'Bug': 2, 'Steel': 0.5},
				'Ghost': {'Normal': 0, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5},
				'Dragon': {'Dragon': 2, 'Steel': 0.5, 'Fairy': 0},
				'Dark': {'Fighting': 0.5, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5, 'Fairy': 0.5},
				'Steel': {'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Ice': 2, 'Rock': 2, 'Steel': 0.5, 'Fairy': 2},
				'Fairy': {'Fire': 0.5, 'Fighting': 2, 'Poison': 0.5, 'Dragon': 2, 'Dark': 2, 'Steel': 0.5}
				}
	
	#TODO: this only works for single battle, we need to modify this later if we expand to double/triple battle
	targetchart = {'specific-move': OTHER,
				   'selected-pokemon-me-first': OPPONENT,
				   'ally': ALLY,
				   'users-field': PLAYER,
				   'user-or-ally': PLAYER,
				   'opponents-field': OPPONENT,
				   'user': PLAYER,
				   'random-opponent': OPPONENT,
				   'all-other-pokemon': OPPONENT,
				   'selected-pokemon': OPPONENT,
				   'all-opponents': OPPONENT,
				   'entire-field': ALL,
				   'user-and-allies': PLAYER, #change later
				   'all-pokemon': ALL
				   }
				
	def __init__(self, name):
		self.name = name
		cur.execute('''
		SELECT type, damage_class, power, accuracy, PP, priority, stat_boosts, effect_chance, target
		FROM Moves WHERE formatted_name = ?
		''', (name, ))
		self.type, self.damage_class, self.power, self.accuracy, self.PP, self.priority, self.stat_boosts, self.effect_chance, self.target = cur.fetchone() #Unpack the results of our query, which is a tuple
		if self.power == None:
			self.power = 0
		else:
			self.power = self.power # Remember that we stored the accuracy and power as strings in case we had null for either of them
		
		if self.accuracy == None:
			self.accuracy = -1 # To the program, we will represent moves that cannot miss as having -1 accuracy. This will make our checking easier. The user will be unaware, of course
		else:
			self.accuracy = int(self.accuracy)
		#print(Move.targetchart[self.target])
	
	def hasStatChange(self):
		return 0x66666 != self.stat_boosts
		
	def getTarget(self): # Trainer or Opponent or Ally?
		return Move.targetchart[self.target]
		