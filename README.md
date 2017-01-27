<h1> Pokémon Simulator </h1>
<h3> Text-based (for the time being) simulator of the Challenge Cup format in Pokémon. </h3>
<ul>
<li> In this format, teams are composed of random Pokémon, random moves, and random stats. </li>
<li> Written in Python </li>
<li> Uses the RESTful API of pokeapi.co to pull data of Pokémon </li>
<li> Caches Pokémon using sqlite3 into a database to avoid the cost of repeatedly fetching pages </li>
</ul>

<ul> <h3> CONTENTS: </h3>
<li> test.py: driver of game </li>
<li> test_classes.py: implementation of the game </li>
<li> load_moves.py: insert Moves into database </li>
<li> load_types.py: insert types of Pokemon into database (deprecated, no longer necessary) </li>
</ul>

<ul> <h3> TO DO: </h3>
<li> Various battle and move effects - OF MAIN IMPORTANCE </li>
<li> Effort values and individual values </li>
<li> Priority </li>
<li> Natures </li>
</ul>

<ul> <h3> COMPLETED FUNCTIONALITY: </h3>
<li> 1/26/2017 - Moves that change stat changes now do so, albeit always changing the stats of the Pokémon using them </li>
<li> 11/11/2016 - Pokemon now have random moves from the pool of moves they can potentially learn using many to many relationship </li>
<li> 11/04/2016 - Types and type matchups, move damage classes, switching </li>
<li> 11/01/2016 - Shell and interaction created, establishes player vs. AI, simple priority calculations, damage calculations, full caching of Pokemon </li>
</ul>
