import re

def count_words(text: str) -> int:
    """
    So‘z sanash qoidalari:
    - o‘, g‘, ng, o`, g` → so‘z hisoblanadi
    - tireli so‘zlar (ilmiy-texnik) → 1 so‘z
    - raqam va emoji hisoblanmaydi
    """
    words = re.findall(r"\b[а-яА-Яa-zA-Z‘’`'-]+\b", text)
    return len(words)
