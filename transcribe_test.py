import os
from faster_whisper import WhisperModel

АУДИО = "Голос 002.m4a"   # <-- замени на имя своего файла

if not os.path.exists(АУДИО):
    print(f"Файл не найден: {АУДИО}")
    print("Положи аудио в папку Ai или проверь имя.")
    exit(1)

print("Загружаю модель (при первом запуске скачается ~1.5 ГБ, подожди)...")
модель = WhisperModel("medium", device="cpu", compute_type="int8")

print("Распознаю, подожди...")
сегменты, инфо = модель.transcribe(АУДИО, language="ru", beam_size=5)

print(f"\nЯзык: {инфо.language} (уверенность: {инфо.language_probability:.2f})")
print("\nТекст:")
текст = ""
for с in сегменты:
    print(с.text, end=" ", flush=True)
    текст += с.text + " "

with open("распознано.txt", "w", encoding="utf-8") as f:
    f.write(текст.strip())
print("\n\nСохранено в распознано.txt")