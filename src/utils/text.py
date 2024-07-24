import re


def strip_excess_whitespace(text: str) -> list[str]:
    cleaned_string = re.sub(r'\s+T$', '', text).strip()
    parts = re.split(r'\s{2,}', cleaned_string)
    return parts
