import urllib.request
import sqlite3
import json
import time

SERVICEURL = 'http://pokeapi.co/api/v2/'
def main():
	conn = sqlite3.connect('cache.db')
	cur = conn.cursor()
	cur.executescript('''
	CREATE TABLE IF NOT EXISTS MovesManager (
		pokemon_id INTEGER,
		move_id INTEGER,
		PRIMARY KEY(pokemon_id, move_id)
	);
	
	CREATE TABLE IF NOT EXISTS Moves (
		id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		noformatName TEXT NOT NULL,
		name TEXT NOT NULL,
		type TEXT NOT NULL,
		damageClass TEXT NOT NULL,
		basePower TEXT,
		accuracy TEXT,
		PP INTEGER NOT NULL,
		priority INTEGER NOT NULL
	);
	''')
	
	cur.execute('''
	SELECT name, id FROM BasePokemon ORDER BY id
	''')
	for name, pokemon_id in cur.fetchall():
		cur.execute('''
		SELECT * FROM MovesManager WHERE pokemon_id=? LIMIT 1
		''', (pokemon_id, ))
		if cur.fetchone() == None:
			print('Generating moves for {}...'.format(name))
		else:
			print('{} already processed...'.format(name))
			continue
			
		req = urllib.request.Request(
			'{}pokemon/{}/'.format(SERVICEURL, name.lower()),
			data=None,
			headers={
				'User-Agent': 'Chrome/54.0.2840.71'
			}
		)
		contents = urllib.request.urlopen(req).read().decode('utf-8')
		js = json.loads(str(contents))
		
		for move in js['moves']:
			movename = move['move']['name']
			cur.execute('''SELECT id FROM Moves where noformatName=?
			''', (movename, ))
			move_id = cur.fetchone()
			if move_id == None:
				req = urllib.request.Request(
					move['move']['url'],
					data=None,
					headers={
						'User-Agent': 'Chrome/54.0.2840.71'
					}
				)
				contents = urllib.request.urlopen(req).read().decode('utf-8')
				jsmoves = json.loads(str(contents))
				print('Inserting {} into database...'.format(jsmoves['names'][0]['name']))

				cur.execute('''INSERT INTO Moves (noformatName, name, type, damageClass, basePower, accuracy, PP, priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
				''', (movename, jsmoves['names'][0]['name'], jsmoves['type']['name'].capitalize(), jsmoves['damage_class']['name'].capitalize(), jsmoves['power'], jsmoves['accuracy'], jsmoves['pp'], jsmoves['priority']))
				cur.execute('''SELECT id FROM Moves where noformatName=?
				''', (movename, ))
				cur.execute('''INSERT INTO MovesManager(pokemon_id, move_id) VALUES (?, ?)
				''', (pokemon_id, cur.fetchone()[0]))
			else:
				cur.execute('''INSERT INTO MovesManager(pokemon_id, move_id) VALUES (?, ?)
				''', (pokemon_id, move_id[0]))
		print()
		conn.commit()
		time.sleep(60)
	
if __name__ == "__main__":
	main()