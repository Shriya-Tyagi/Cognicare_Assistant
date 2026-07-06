from GroveLCDriver import GroveLcd
from Voices import get_mood

MOOD_FACE: dict[str, str] = {
    "Happy":   ";)",
    "Smile":   ":)",
    "Concern": ";/",
    "Sad":     ";0",
}

def main() -> None:
    mood = get_mood()
    face = MOOD_FACE.get(mood)

    if face is None:
        face = ":]"
        
    with GroveLcd() as lcd:
        lcd.write(face)

        
if __name__ == "__main__":
    main()
