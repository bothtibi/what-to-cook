# What to Cook (Streamlit MVP)

Simple Streamlit app that suggests recipes based on your ingredients.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

- `app.py` - Streamlit entry point/UI
- `utils/recipe_service.py` - recipe loading and filtering logic
- `data/recipes.json` - small local dataset for MVP
- `requirements.txt` - minimal dependency list
