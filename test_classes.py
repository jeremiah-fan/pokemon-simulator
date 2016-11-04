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
cur.executescript('''
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
''')
		
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
		print('What will {} do?\n'.format(player_pkmn.name))
	
	def priority(self, player_pkmn, opponent_pkmn):
		if player_pkmn.stats[Pokemon.SPD] > opponent_pkmn.stats[Pokemon.SPD]:
			return (player_pkmn, opponent_pkmn)
		elif player_pkmn.stats[Pokemon.SPD] < opponent_pkmn.stats[Pokemon.SPD]:
			return (opponent_pkmn, player_pkmn)
		else:
			options = [(player_pkmn, opponent_pkmn), (opponent_pkmn, player_pkmn)]
			return random.choice(options) #Speed Tie, ordering is randomly determined
	
	def execMove(self, player, move, receiver):
		if move == None:
			return 1
		pkmn = player.getCurPkmn()
		rcvPkmn = receiver.getCurPkmn()
		attackmsg = '{} used {}!'.format(pkmn.name, move.name)
		if player.type == Trainer.OPPONENT:
			attackmsg = 'The opposing {}'.format(attackmsg)
		print(attackmsg)
		if pkmn.inflictdmg(move, rcvPkmn) == True:
			faintmsg = '{} fainted!'.format(rcvPkmn.name)
			if receiver.type == Trainer.OPPONENT:
				faintmsg = 'The opposing {}'.format(faintmsg)
			print(faintmsg)
			receiver.sendNewPkmn()
			if receiver.getNumPkmn() == 0:
				if receiver.type == Trainer.OPPONENT:
					print('You defeated {}!'.format(receiver.name))
				else:
					print('You lost to {}!'.format(player.name))
				self.gameover = True
			else:
				print('{} sent out {}!'.format(receiver.name, receiver.getCurPkmn().name))
			return 0 #Turn ends
		return 1 #Turn continues
	
	def turn(self):
		self.gameturn += 1
		self.display()
		ordering = self.priority(self._player.getCurPkmn(), self._opponent.getCurPkmn()) #Tuple of two Pokemon
		moves = (ordering[0].getTrainer().getMove(), ordering[1].getTrainer().getMove())
		if self.execMove(ordering[0].getTrainer(), moves[0], ordering[1].getTrainer()) == 1:
			self.execMove(ordering[1].getTrainer(), moves[1], ordering[0].getTrainer())	

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
	
	def getCurPkmn(self):
		return self._trainer_pkmn[self.cur_pkmn_index]
		
	def getNumPkmn(self):
		return Trainer.NUM_PKMN - self.cur_pkmn_index
		
	def sendNewPkmn(self):
		self.cur_pkmn_index += 1
		
	def showPkmn(self):
		for pkmn in self._trainer_pkmn:
			print('{name} Lv. {lv}\n{type}\n{curHP}/{maxHP}'.format(name=pkmn.name, lv=pkmn.level, type='/'.join([x for x in pkmn.type if x != None]), curHP=pkmn.stats[Pokemon.HP], maxHP=pkmn.maxHP))
		print()
	
	def switch(self, pkmn):
		pkmn_index = self._trainer_pkmn.index(pkmn)
		self._trainer_pkmn[self.cur_pkmn_index], self._trainer_pkmn[pkmn_index] = self._trainer_pkmn[pkmn_index], self._trainer_pkmn[self.cur_pkmn_index]
	
	def getMove(self):
		pkmn = self.getCurPkmn()
		if self.type == Trainer.OPPONENT:
			return random.choice(pkmn.moves)
		while True:
			movenum = input('{0}(1) {1}(2) {2}(3) {3}(4) Party(p): '.format(pkmn.moves[0].name, pkmn.moves[1].name, pkmn.moves[2].name, pkmn.moves[3].name))
			if movenum.isdigit() and int(movenum) >= 1 and int(movenum) <= 4:
				return pkmn.moves[int(movenum) - 1]
			elif movenum == 'p':
				self.showPkmn()
				goback = False
				while True:
					pkmnname = input('Pokemon to switch to: (press b to go back)')
					if pkmnname == 'b':
						goback = True
						break
					find = [x for x in self._trainer_pkmn if x.name == pkmnname.capitalize()]
					if len(find) > 0:
						pkmn = find[0]
						if pkmn.stats[Pokemon.HP] > 0:
							print('{trainer} withdrew {name}!'.format(trainer=self.name, name=self.getCurPkmn().name))
							self.switch(pkmn)
							print('{trainer} sent out {name}!'.format(trainer=self.name, name=self.getCurPkmn().name))
							break
						print('That Pokemon is too weak to fight!')
					print('Not a valid Pokemon name, try again')
				if goback == False:
					return None
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
	
	def __init__(self, name, trainer):
		self.trainer = trainer
		self.name = name
		self.faint = False
		self.moves = [Move('Tackle')] * Pokemon.NUM_MOVES
		self.level = 50
		cur.execute('''
		SELECT type1, type2, baseHP, baseATT, baseDEF, baseSPATT, baseSPDEF, baseSPD FROM BasePokemon WHERE name = ?
		''', (name, ))
		queryresults = cur.fetchone()
		self.type = (queryresults[0], queryresults[1])
		basestats = list(queryresults[2:])
		self.stats = [(x * 2 + 31) * self.level // 100 + 5 for x in basestats]
		self.stats[0] += self.level + 5
		self.maxHP = self.stats[0]
	
	def getTrainer(self):
		return self.trainer
	
	def inflictdmg(self, move, pkmn):
		if move.damage_class == "physical":
			attstat = Pokemon.ATT
			defstat = Pokemon.DEF
		else: #if move is special, use the special att and special def stats to calculate dmg
			attstat = Pokemon.SPATT
			defstat = Pokemon.SPDEF
		#damage formula, not accounting for STAB and type and the weird small modifiers
		dmg = (((2 * self.level + 10) / 250) * (self.stats[attstat] / pkmn.stats[defstat]) * move.power + 2) * random.uniform(0.85, 1)
		
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
		
		if random.random() < 0.0625:
			print('A critical hit!')
			dmg *= 1.5 #specific to generation VI
		
		return pkmn.takedmg(int(dmg))
	
	def takedmg(self, amt):
		self.stats[Pokemon.HP] = max(0, self.stats[Pokemon.HP] - amt)
		if self.stats[Pokemon.HP] == 0:
			self.faint = True
		return self.faint

class Move:
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
				
	def __init__(self, name):
		self.name = name
		self.power = 50
		self.type = 'Normal'
		self.damage_class = 'physical'
		