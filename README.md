# Cognicare_Assistant: Jack

Jack is a Raspberry Pi voice assistant built around a local language model running through Ollama. It combines speech recognition, text-to-speech, basic audio signal processing, and GPIO peripherals into a single embedded application.

The project began as an exploration of running an LLM on inexpensive hardware and integrating it with physical sensors for our ECE 198 project design.

Features

* Wake-word activation
* Local LLM inference through Ollama
* Speech-to-text/Text-to-speech
* Conversation history
* Daily chat logging
* Audio normalization
* Simple audio analysis for distress detection
* Sensors for distress detection
* GPIO buzzer output

Hardware

Developed on a Raspberry Pi with:
* USB microphone
* Speaker
* GPIO buzzer
* Grove RGB LCD
* DHT temperature/humidity sensor
* MAX30102 pulse oximeter
* Grove sound sensor

The assistant records audio, waits for the wake word, sends requests to the local model, and speaks responses through the configured TTS engine.

Notes

The distress detection component is intentionally simple. It uses volume and dominant frequency as demonstration heuristics for triggering external hardware and should not be interpreted as reliable emotion detection. Sensors used are not precise, should be upgraded, and their heuristic math should also be upgraded alongside. Current math assumes sesnors are somewhat innaccurate.
