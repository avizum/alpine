def singular_plural(number: int, word: str):
    if number == 1:
        result = f"{number} {word}"
    else:
        result = f"{number} {word}s"
        return result
