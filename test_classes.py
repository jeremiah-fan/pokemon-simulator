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
		pkmn = player.getCurPkmn()
		rcvPkmn = receiver.getCurPkmn()
		attackmsg = '{} used {}!'.format(pkmn.name, move.name)
		if player.type == Trainer.OPPONENT:
			attackmsg = 'The opposing {}'.format(attackmsg)
		print(attackmsg)
		if rcvPkmn.takedmg(move.power) == True:
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
					pkmnname = input('Pokemon #{}: '.format(num + 1))
					if pkmnname.strip() != '' and not pkmnname.isdigit():
						cur.execute('''
						SELECT name, baseHP, baseATT, baseDEF, baseSPATT, baseSPDEF, baseSPD FROM BasePokemon WHERE name = ?
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
							js = json.loads(str(contents))
							stats = js['stats']
							cur.execute('''
							INSERT INTO BasePokemon(name, baseHP, baseATT, baseDEF, baseSPATT, baseSPDEF, baseSPD) VALUES (?, ?, ?, ?, ?, ?, ?)
							''', (pkmnname.capitalize(), stats[5]['base_stat'], stats[4]['base_stat'], stats[3]['base_stat'], stats[2]['base_stat'], stats[1]['base_stat'], stats[0]['base_stat']))
							break
						except:
							print('Not a valid Pokemon name, try again')
							continue
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
			print('{} Lv. {}\n{}/{}'.format(pkmn.name, pkmn.level, pkmn.stats[Pokemon.HP], pkmn.maxHP))
		print()
	
	def getMove(self):
		pkmn = self.getCurPkmn()
		if self.type == Trainer.OPPONENT:
			return random.choice(pkmn.moves)
		while True:
			movenum = input('{}(1) {}(2) {}(3) {}(4) Party(p): '.format(pkmn.moves[0].name, pkmn.moves[1].name, pkmn.moves[2].name, pkmn.moves[3].name))
			if movenum.isdigit() and int(movenum) >= 1 and int(movenum) <= 4:
				return pkmn.moves[int(movenum) - 1]
			elif movenum == 'p':
				self.showPkmn()
				
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
		self.moves = [Move('test')] * Pokemon.NUM_MOVES
		self.level = 50
		cur.execute('''
		SELECT name, baseHP, baseATT, baseDEF, baseSPATT, baseSPDEF, baseSPD FROM BasePokemon WHERE name = ?
		''', (name, ))
		basestats = list(cur.fetchone()[1:])
		self.stats = [(x * 2 + 31) * self.level // 100 + 5 for x in basestats]
		self.stats[0] += self.level + 5
		self.maxHP = self.stats[0]
	
	def getTrainer(self):
		return self.trainer
			
	def takedmg(self, amt):
		self.stats[Pokemon.HP] = max(0, self.stats[Pokemon.HP] - amt)
		if self.stats[Pokemon.HP] == 0:
			self.faint = True
		return self.faint

class Move:
	def __init__(self, name):
		self.name = name
		self.power = 50
		self.damage_class = 'physical'	
		