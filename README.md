# Csaladi fozes es receptkoveto (V2)

Egyszeru, magyar nyelvu Streamlit app:
- recept CRUD
- ajanlo (single + leves/foetel kombinacio)
- history (lista + idovonal nezet)
- JSON backup export/import
- egyszeru shared login

## Local futtatas

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit secrets (opcionalis)

Alapertelmezetten local fallback ertekeket hasznal. Deploymenthez ajanlott:

- `APP_USERNAME`
- `APP_PASSWORD`
- `DB_PATH` (pl. `data/app.db`)
- `TURSO_DATABASE_URL` (ha Turso-t hasznalsz)
- `TURSO_AUTH_TOKEN` (ha Turso-t hasznalsz)

Ha a Turso URL + token be van allitva es a `libsql-client` telepitve van, az app Turso-t hasznal.
Ellenkezo esetben automatikusan a lokalis SQLite fallback (`DB_PATH`) marad aktiv.

## Projekt struktura

- `app.py` - belepesi pont, menu, oldalak
- `src/auth.py` - login/session
- `src/db.py` - SQLite kapcsolat es tabla init
- `src/recipes.py` - recipe CRUD + kereses
- `src/history.py` - history mentes/listazas
- `src/recommendations.py` - MVP ajanlo scoring
- `src/backup.py` - JSON export/import
- `src/ui/*` - Streamlit oldalak
