import urllib.request
import sqlite3
import json

SERVICEURL = 'http://pokeapi.co/api/v2/'
def main():
	conn = sqlite3.connect('cache.db')
	cur = conn.cursor()
	cur.executescript('''
	ALTER TABLE BasePokemon RENAME TO Temp;
	CREATE TABLE BasePokemon (
		id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		name TEXT,
		type1 TEXT DEFAULT '',
		type2 TEXT DEFAULT '',
		baseHP INTEGER NOT NULL,
		baseATT INTEGER NOT NULL,
		baseDEF INTEGER NOT NULL,
		baseSPATT INTEGER NOT NULL,
		baseSPDEF INTEGER NOT NULL,
		baseSPD INTEGER NOT NULL
	);
	INSERT INTO BasePokemon (id, name, baseHP, baseATT, baseDEF, baseSPATT, baseSPDEF, baseSPD)
	SELECT id, name, baseHP, baseATT, baseDEF, baseSPATT, baseSPDEF, baseSPD FROM Temp;
	DROP TABLE Temp;
	''')
	
	cur.execute('''
	SELECT seq FROM sqlite_sequence WHERE name='BasePokemon'
	''')
	for i in range(1, cur.fetchone()[0] + 1):
		cur.execute('''
		SELECT name FROM BasePokemon WHERE id=?
		''', (i, ))
		name = cur.fetchone()[0]
		print('Modifying {}...'.format(name))
		req = urllib.request.Request(
			'{}pokemon/{}/'.format(SERVICEURL, name.lower()),
			data=None,
			headers={
				'User-Agent': 'Chrome/54.0.2840.71'
			}
		)
		contents = urllib.request.urlopen(req).read().decode('utf-8')
		js = json.loads(str(contents))
		types = js['types']
		if len(types) == 2: #Dual typing
			type1 = types[1]['type']['name'].capitalize()
			type2 = types[0]['type']['name'].capitalize()
		else:
			type1 = types[0]['type']['name'].capitalize()
			type2 = None
		cur.execute('''UPDATE BasePokemon SET type1=?, type2=? WHERE id=?
		''', (type1, type2, i))	
		
	conn.commit()
	
if __name__ == "__main__":
	main()