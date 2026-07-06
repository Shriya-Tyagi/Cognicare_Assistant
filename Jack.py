import ollama
from faster_whisper import WhisperModel
import pyttsx3
import os
import pyaudio
import time
import wave
import audioop
import subprocess
from pathlib import Path
import numpy as np
from datetime import date
from scipy.fft import rfft, rfftfreq

# SETTINGS

OLLAMA_MODEL = "gpt-oss:20b"

WAKE_WORD = "jack"

PANIC_VOLUME_THRESHOLD = 12000
PANIC_FREQ_THRESHOLD = 2500

RECORD_SECONDS = 5
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

MAX_MESSAGES = 12

RAW_AUDIO_FILE = "temp.wav"
CLEAN_AUDIO_FILE = "clean.wav"

GPIO_PIN = 18

today = str(date.today())
LOG_FILE = Path(f"chatlog-{today}.txt")


# TTS

engine = pyttsx3.init()
engine.setProperty('rate', 190)

voices = engine.getProperty("voices")
if len(voices) > 1:
    engine.setProperty("voice", voices[1].id)

# SPEAK

def speak_text(text: str) -> None:
    print("AI:", text)
    engine.say(text)
    engine.runAndWait()


# LOCAL STT

stt_model = WhisperModel(
    "base.en",
    device="cpu",
    compute_type="int8",
)

def transcribe_audio(filename: str) -> str:
    segments, _ = stt_model.transcribe(filename, language="en")

    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )

    return text.strip()


# OLLAMA CHAT

def new_conversation() -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are Jack, a concise voice assistant running locally "
                "on a Raspberry Pi. Keep responses short and speakable."
            ),
        }
    ]


def trim_talk(talk: list[dict[str, str]]) -> list[dict[str, str]]:
    if talk and talk[0]["role"] == "system":
        return [talk[0]] + talk[1:][-MAX_MESSAGES:]

    return talk[-MAX_MESSAGES:]


def chatfun(talk: list[dict[str, str]]) -> list[dict[str, str]]:
    talk = trim_talk(talk)

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=talk,
        options={
            "temperature": 0.7,
            "num_predict": 120,
        },
    )

    ai_reply = response["message"]["content"].strip()

    talk.append(
        {
            "role": "assistant",
            "content": ai_reply,
        }
    )

    return trim_talk(talk)


# LOGGING

def append2log(text: str) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(text + "\n")

# RECORD AUDIO

def record_audio(filename: str = RAW_AUDIO_FILE) -> str:
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    frames = []

    try:
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
    finally:
        stream.stop_stream()
        stream.close()

    sample_width = p.get_sample_size(FORMAT)
    p.terminate()

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(sample_width)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))

    return filename


def normalize_audio(
    input_file: str,
    output_file: str = CLEAN_AUDIO_FILE,
) -> str:
    subprocess.run(
        [
            "sox",
            input_file,
            output_file,
            "gain",
            "-n",
            "silence",
            "1",
            "0.1",
            "1%",
            "reverse",
            "silence",
            "1",
            "0.1",
            "1%",
            "reverse",
        ],
        check=True,
    )

    return output_file


def analyze_audio(filename: str) -> tuple[int, float]:
    with wave.open(filename, "rb") as wf:
        frames = wf.readframes(wf.getnframes())

    # loudness
    rms = audioop.rms(frames, 2)

    # pitch
    samples = np.frombuffer(frames, dtype=np.int16)

    if len(samples) == 0:
        return rms, 0.0

    yf = np.abs(rfft(samples))
    xf = rfftfreq(len(samples), 1 / RATE)

    dominant_freq = float(xf[np.argmax(yf)])

    return rms, dominant_freq


# DISTRESS DETECTION

def distress_detected(volume: int, freq: float) -> bool:
    if volume > PANIC_VOLUME_THRESHOLD:
        return True

    if freq > PANIC_FREQ_THRESHOLD:
        return True

    return False

# BUZZER

def activate_buzzer() -> None:
    # PI GPIO PIN 18
    os.system("gpio -g mode 18 out")

    for _ in range(3):
        os.system("gpio -g write 18 1")
        time.sleep(0.2)

        os.system("gpio -g write 18 0")
        time.sleep(0.2)

# REQUEST PARSING

def extract_wake_request(text: str) -> str | None:
    lowered = text.lower()

    if WAKE_WORD not in lowered:
        return None

    return lowered.split(WAKE_WORD, 1)[1].strip()


def should_sleep(request: str) -> bool:
    return any(
        phrase in request
        for phrase in [
            "go to sleep",
            "bye jack",
        ]
    )


# MAIN

def main() -> None:
    talk: list[dict[str, str]] = []
    sleeping = True

    print("Jack is running.")

    while True:
        try:
            print("\nListening...")

            raw_audio = record_audio()
            clean_audio = normalize_audio(raw_audio)

            volume, freq = analyze_audio(clean_audio)

            print(f"Volume: {volume}")
            print(f"Pitch: {freq:.1f}")

            if distress_detected(volume, freq):
                print("DISTRESS DETECTED")
                activate_buzzer()

            text = transcribe_audio(clean_audio)

            if not text:
                print("No speech detected.")
                continue

            print("You:", text)

            if sleeping:
                request = extract_wake_request(text)

                if request is None:
                    continue

                sleeping = False
                talk = new_conversation()

                if len(request) < 3:
                    speak_text("How can I help?")
                    continue

            else:
                request = text.lower().strip()

                if should_sleep(request):
                    speak_text("Bye now.")
                    sleeping = True
                    talk = []
                    continue

                wake_request = extract_wake_request(request)
                if wake_request:
                    request = wake_request

            append2log(f"You: {request}")

            talk.append(
                {
                    "role": "user",
                    "content": request,
                }
            )

            talk = chatfun(talk)

            ai_text = talk[-1]["content"].strip()

            append2log(f"AI: {ai_text}")

            speak_text(ai_text)

if __name__ == "__main__":
    main()
