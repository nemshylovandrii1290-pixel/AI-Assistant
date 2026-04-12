from rapidfuzz import fuzz

from backend.utils.normalize import normalize_text


def contains_phrase(text, phrases, threshold=85):
    normalized_text = normalize_text(text)
    if not normalized_text:
        return False

    text_words = normalized_text.split()

    for phrase in phrases:
        normalized_phrase = normalize_text(phrase)
        if normalized_phrase in normalized_text:
            return True

        phrase_words = normalized_phrase.split()
        if phrase_words and all(
            any(fuzz.ratio(word, text_word) >= threshold for text_word in text_words)
            for word in phrase_words
        ):
            return True

        if len(phrase_words) <= 1:
            if fuzz.partial_ratio(normalized_text, normalized_phrase) >= threshold:
                return True

            if fuzz.partial_ratio(normalized_phrase, normalized_text) >= threshold:
                return True

    return False
