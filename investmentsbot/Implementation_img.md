# Implementation Plan: Refactor Showcase Image Logic

This plan describes how to move the showcase image URL from hardcoded values in `main.py` to the `.env` configuration file. This allows for easier updates without modifying the code.

## 1. Update `.env`

Add the `SHOWCASE_IMAGE_URL` variable to your `.env` file. You can set this to any accessible image URL.

```env
SHOWCASE_IMAGE_URL=https://i.postimg.cc/T2thBcsP/photo-2025-08-01-21-47-44.jpg
```

## 2. Update `config.py`

Add code to load this variable.

**Open `config.py` and add:**

```python
SHOWCASE_IMAGE_URL = os.getenv("SHOWCASE_IMAGE_URL", "https://i.postimg.cc/T2thBcsP/photo-2025-08-01-21-47-44.jpg")
```

## 3. Update `main.py`

Modify `main.py` to import and use this new configuration variable.

**A. Import the variable:**

Find the line importing from `config` (usually near the top) and add `SHOWCASE_IMAGE_URL`.

```python
from config import BOT_TOKEN, ..., SHOWCASE_IMAGE_URL
```

**B. Update `send_showcase` function:**

Find the `send_showcase` function and replace the hardcoded `photo_url` assignment.

```python
async def send_showcase(chat_id: int):
    # ... (previous code) ...
    
    # OLD:
    # photo_url = "https://i.postimg.cc/T2thBcsP/photo-2025-08-01-21-47-44.jpg"
    
    # NEW:
    photo_url = SHOWCASE_IMAGE_URL
    
    # ... (rest of the function) ...
```
