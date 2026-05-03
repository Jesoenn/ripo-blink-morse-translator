from spellchecker import SpellChecker
import re

try:
    import language_tool_python
    LANGUAGE_TOOL_AVAILABLE = True
except ImportError:
    LANGUAGE_TOOL_AVAILABLE = False

# Simple Polish dictionary for common corrections (can be expanded)
POLISH_CORRECTIONS = {
    'witim': 'witamy',
    'witaj': 'witaj',
    'czesc': 'cześć',
    'dzieki': 'dzięki',
    'prosze': 'proszę',
    'zycze': 'życzę',
    'pozytywnie': 'pozytywnie',
    'bezpieczenstwo': 'bezpieczeństwo',
    # Add more as needed
}

class Autocorrector:
    def __init__(self, language='en', debug=False):
        self.debug = debug
        self.language = language
        self.spell = None
        self.tool = None
        self.polish_mode = (language == 'pl')
        
        if self.polish_mode and LANGUAGE_TOOL_AVAILABLE:
            try:
                self.tool = language_tool_python.LanguageTool('pl-PL')
                if self.debug:
                    print("[Autocorrector] Loaded LanguageTool for Polish (pl-PL)")
            except Exception as e:
                if self.debug:
                    print(f"[Autocorrector] Failed to load LanguageTool: {e}")
                    print("[Autocorrector] Falling back to dictionary-based corrections")
                self.tool = None
        
        if not self.polish_mode:
            try:
                self.spell = SpellChecker(language=language)
                if self.debug:
                    print(f"[Autocorrector] Loaded dictionary for {language}")
            except ValueError as e:
                if self.debug:
                    print(f"[Autocorrector] Language {language} not supported: {e}")
                    print("[Autocorrector] Falling back to English")
                try:
                    self.spell = SpellChecker(language='en')
                    self.language = 'en'
                except Exception as e2:
                    if self.debug:
                        print(f"[Autocorrector] Failed to load any dictionary: {e2}")
                    self.spell = None
                    self.language = None

    def correct_text(self, text):
        if not text:
            return text
        text = text.strip()
        if not text:
            return text
        
        if self.polish_mode:
            return self._correct_polish(text)
        else:
            return self._correct_english(text)

    def _correct_polish(self, text):
        text = text.strip()
        if not text:
            return text

        # Try LanguageTool first if available
        if self.tool:
            try:
                matches = self.tool.check(text)
                if matches:
                    corrected = language_tool_python.utils.correct(text, matches)
                    if corrected != text and self.debug:
                        print(f"[Autocorrector-LM] '{text}' -> '{corrected}'")
                    return corrected
            except Exception as e:
                if self.debug:
                    print(f"[Autocorrector-LM] Error: {e}")
        
        # Fallback to dictionary
        words = text.split()
        corrected_words = []
        
        for word in words:
            # remove trailing punctuation
            trailing_punct = ''
            clean_word = word
            while clean_word and not clean_word[-1].isalpha():
                trailing_punct = clean_word[-1] + trailing_punct
                clean_word = clean_word[:-1]
            
            # check dictionary first (case-insensitive)
            lower_word = clean_word.lower()
            if lower_word in POLISH_CORRECTIONS:
                corrected = POLISH_CORRECTIONS[lower_word]
                corrected_words.append(corrected + trailing_punct)
                if self.debug:
                    print(f"[Autocorrector-PL] '{clean_word}' -> '{corrected}'")
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)

    def _correct_english(self, text):
        if not self.spell:
            return text

        text = text.strip()
        if not text:
            return text
            
        words = text.split()
        corrected_words = []
        
        for word in words:
            # remove trailing punctuation
            trailing_punct = ''
            clean_word = word
            while clean_word and not clean_word[-1].isalpha():
                trailing_punct = clean_word[-1] + trailing_punct
                clean_word = clean_word[:-1]
            
            if len(clean_word) > 1:
                # try to correct
                cand = self.spell.correction(clean_word)
                if cand and cand != clean_word:
                    corrected_words.append(cand + trailing_punct)
                    if self.debug:
                        print(f"[Autocorrector-EN] '{clean_word}' -> '{cand}'")
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)

    # Placeholder for future context-aware LM integration
    def correct_with_lm(self, text, lm_callable=None):
        if lm_callable is None:
            return self.correct_text(text)
        # lm_callable should be a function that accepts text and returns corrected text
        return lm_callable(text)
