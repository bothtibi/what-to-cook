Családi főzés- és receptkövető alkalmazás specifikáció
1. Termék célja
Egy egyszerű, magyar nyelvű családi alkalmazás készítése, amely segít eldönteni, hogy mit főzzünk.
Az app fő célja nem az, hogy bonyolult készletnyilvántartó vagy étkezéstervező rendszer legyen, hanem hogy:
•	tárolja a családi recepteket,
•	kövesse, mikor mit főztünk,
•	megmutassa, mi volt mostanában,
•	ajánljon levest, főételt vagy komplett ebédkombinációt,
•	csökkentse a napi “mit főzzünk?” döntési fáradtságot.
Az alkalmazást két ember használja: férj és feleség. Nem kell többfelhasználós családi rendszer, regisztráció vagy jogosultsági modell.
2. Technológiai irány
Javasolt MVP stack:
•	Python
•	Streamlit
•	Turso / libSQL adatbázis
•	Streamlit Community Cloud hosting
•	GitHub repository
•	egyszerű saját login
•	magyar UI
Fejlesztési workflow:
•	Cursor alapú AI-assisted fejlesztés
•	prompt alapú iteráció
•	lokális review
•	GitHub push
•	automatikus Streamlit deploy
3. Fő product elvek
3.1 Egyszerűség
Az app használata ne vegyen el sok időt.
3.2 Nem készletnyilvántartó
Nem kell pontosan trackelni:
•	mennyi leves maradt,
•	hány adag van még,
•	mikor fogyott el teljesen.
A user csak azt rögzíti:
•	mit főzött,
•	mikor főzte,
•	kb. hány napra főzte.
3.3 Az adat a legfontosabb
A hosting újratelepíthető, a kód GitHubról visszaállítható, de az adatbázis kritikus asset.
4. Felhasználók
MVP-ben egyetlen közös account:
•	username
•	password
Nincs:
•	regisztráció,
•	role management,
•	több user.
5. Kategóriák
Fix kategóriák:
•	leves
•	főétel
•	reggeli
•	vacsora
6. Tagek
Dinamikus tagek:
•	savanyú
•	húsos
•	gyors
•	olcsó
•	sütős
•	téli
•	nyári
Nem előre definiált lista.
7. Recept adatmodell
Recipe mezők:
•	id
•	name
•	category
•	tags
•	prep_time_minutes
•	difficulty
•	ingredients_text
•	instructions_text
•	notes_text
•	is_favorite
•	is_blocked
•	created_at
•	updated_at
8. History modell
CookingHistoryEntry:
•	recipe_id
•	cooked_date
•	days_planned
•	quantity_note
•	meal_group_id
•	notes
9. Fő use case-ek
•	új recept hozzáadása
•	recept szerkesztése
•	recept keresése
•	“Mit főzzünk?” ajánló
•	history rögzítés
•	backup export
10. Ajánló MVP logika
Szempontok:
•	rég volt
•	ne legyen túl gyakori
•	kedvencek enyhe előnye
•	tiltott receptek kizárása
•	kategória figyelembevétele
•	kis random faktor
11. Kombinációk
Leves + főétel kombinációk:
•	külön receptek
•	együtt ajánlhatók
•	meal_group segítségével összekapcsolhatók
12. “Ezt megfőztük” flow
Az ajánló ne mentsen automatikusan.
Kell külön:
•	“Ezt megfőztük” gomb
13. History nézet
Nap alapú megjelenítés:
•	mikor mi volt
•	hány napra főztük
•	receptre kattintás
•	keresés és szűrés
14. UI irány
Modern, kártyás, de egyszerű UI.
Fő oldalak:
•	Ajánló
•	Receptek
•	History
•	Backup
•	Beállítások
15. Backup / Export
JSON export:
•	receptek
•	history
•	tagek
•	kombinációk
Később import lehetőség.
16. Adatbázis
Turso / libSQL használata.
17. Projekt struktúra
meal-memory-app/
•	app.py
•	requirements.txt
•	src/
  - auth.py
  - db.py
  - recipes.py
  - history.py
  - recommendations.py
  - backup.py
18. Future AI phase
Hibrid ajánló:
•	lokális scoring
•	LLM integráció
•	ChatGPT/OpenAI API támogatás
19. Acceptance criteria
•	működő recipe CRUD
•	működő history
•	működő ajánló
•	működő keresés
•	backup export
•	login rendszer
