import re
from aiogram import types
from aiogram.filters import BaseFilter
import aiosqlite
from db import DB_FILE

BAD_WORDS = [
    'хуй', 'пизда', 'ебал', 'ебан', 'бля', 'блядь', 'сука', 'гондон', 'мудак',
    'пидор', 'педик', 'шлюха', 'чмо', 'долбоеб', 'залупа', 'пиздец', 'ебать',
    'выебок', 'еблан', 'ебло', 'ебнутый', 'мразь', 'падла', 'ублюдок', 'хуесос',
    'хуйня', 'пиздеть', 'говно', 'дерьмо', 'заебал', 'охуел', 'охуеть', 'сучка',
    'трахать', 'выебываться', 'выебон', 'ебись', 'пиздюк', 'хуила', 'хуйло'
]

BAD_WORD_VARIANTS = {
    'а': ['а', 'a', '@'],
    'б': ['б', '6', 'b'],
    'в': ['в', 'b', 'v'],
    'г': ['г', 'r', 'g'],
    'д': ['д', 'd'],
    'е': ['е', 'e', 'ё'],
    'з': ['з', '3', 'z'],
    'и': ['и', 'u', 'i'],
    'к': ['к', 'k'],
    'л': ['л', 'l'],
    'н': ['н', 'h', 'n'],
    'о': ['о', 'o', '0'],
    'п': ['п', 'n', 'p'],
    'р': ['р', 'p', 'r'],
    'с': ['с', 'c', 's'],
    'т': ['т', 'm', 't'],
    'у': ['у', 'y', 'u'],
    'ф': ['ф', 'f'],
    'х': ['х', 'x', 'h'],
    'ч': ['ч', '4'],
    'ш': ['ш'],
    'щ': ['щ'],
    'ы': ['ы'],
    'ь': ['ь'],
    'ъ': ['ъ'],
    'э': ['э'],
    'ю': ['ю'],
    'я': ['я']
}

class IsBadWord(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        text = message.text or message.caption or ""
        text = text.lower()
        
        for word in BAD_WORDS:
            if word in text:
                return True
        
        for bad_word in BAD_WORDS:
            pattern = ''
            for char in bad_word:
                if char in BAD_WORD_VARIANTS:
                    variants = BAD_WORD_VARIANTS[char]
                    pattern += f'[{"".join(variants)}]'
                else:
                    pattern += char
            
            if re.search(pattern, text):
                return True
        
        for bad_word in BAD_WORDS:
            spaced_pattern = r'\s*'.join([re.escape(c) for c in bad_word])
            if re.search(spaced_pattern, text):
                return True
        
        return False

class IsBlockedUser(BaseFilter):
    async def __call__(self, obj) -> bool:
        user_id = None
        if isinstance(obj, types.Message):
            user_id = obj.from_user.id
        elif isinstance(obj, types.CallbackQuery):
            user_id = obj.from_user.id
        else:
            return False
        
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute("SELECT account_status FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return row and row[0] == 'О'
        
        
def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_phone(phone: str) -> bool:
    pattern = r'^\+?[\d\s\-\(\)]{7,15}$'
    return bool(re.match(pattern, phone))