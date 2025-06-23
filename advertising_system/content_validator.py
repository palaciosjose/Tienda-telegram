class ContentValidator:
    """Simple validator to avoid spam"""
    forbidden = ['spam', 'scam']

    @classmethod
    def is_valid(cls, text):
        lower = text.lower()
        return not any(word in lower for word in cls.forbidden)
