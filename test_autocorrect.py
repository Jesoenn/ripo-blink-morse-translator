from src.autocorrect import Autocorrector

def test_autocorrector():
    corrector = Autocorrector(language='pl', debug=True)

    test_cases = [
        "witim na pokladie",
        "czesc!",
        "Idę jutro do kino",
        "Ala ma kta"
    ]

    for i, original in enumerate(test_cases, 1):
        corrected = corrector.correct_text(original)
        print(f"TEST {i}:")
        print(f"Original: {original}")
        print(f"Result: {corrected}")
        print()


if __name__ == "__main__":
    test_autocorrector()