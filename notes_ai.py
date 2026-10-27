import sys
import os
import glob
import shutil
import ollama
from faster_whisper import WhisperModel

# === НАСТРОЙКИ ===
МОДЕЛЬ = "qwen2.5:7b"
VAULT = r"C:\Users\1\Desktop\Tot\Tree"   # <-- проверь, что путь правильный
ВХОДЯЩИЕ = "Входящие"
WHISPER_РАЗМЕР = "medium"
WHISPER_УСТРОЙСТВО = "cpu"

# === ИИ ===
def спросить_ии(запрос):
    ответ = ollama.chat(
        model=МОДЕЛЬ,
        messages=[{"role": "user", "content": запрос}]
    )
    return ответ["message"]["content"]

# === ФАЙЛЫ ===
def список_папок():
    папки = []
    for корень, подпапки, файлы in os.walk(VAULT):
        подпапки[:] = [п for п in подпапки if not п.startswith(".")]
        for п in подпапки:
            полный = os.path.join(корень, п)
            относительный = os.path.relpath(полный, VAULT)
            if относительный.split(os.sep)[0] == ВХОДЯЩИЕ:
                continue
            папки.append(относительный.replace(os.sep, "/"))
    return папки

def создать_папку():
    имя = input("Название новой папки (можно вложенную, через /): ").strip()
    if not имя:
        print("Пустое имя, отмена.")
        return
    путь = os.path.join(VAULT, имя)
    try:
        os.makedirs(путь, exist_ok=True)
        print(f"Папка создана: {путь}")
    except Exception as e:
        print(f"Ошибка: {e}")

def безопасное_имя(текст):
    return "".join(c for c in текст if c not in '\\/:*?"<>|').strip()

# === РАСКЛАДКА ===
def разложить_конкретную_заметку(путь_файла):
    """Раскладывает один файл-заметку по дереву с помощью ИИ."""
    with open(путь_файла, "r", encoding="utf-8") as f:
        текст = f.read()

    папки = список_папок()
    if not папки:
        print("Нет папок, кроме Входящих. Создай папки сначала.")
        return

    промт = f"""Ты — помощник по сортировке заметок.
Вот список существующих папок:
{chr(10).join('- ' + p for p in папки)}

Вот текст заметки:
\"\"\"
{текст}
\"\"\"

Выбери, в какую папку положить эту заметку, и предложи короткий заголовок для неё (от одного до четырех слов и цифра если нужно)
Ответь СТРОГО в таком формате, без лишних слов:
ПАПКА: <название папки из списка>
ЗАГОЛОВОК: <короткий заголовок>
"""

    print("\nСпрашиваю модель, подожди...")
    ответ = спросить_ии(промт)
    print("\nМодель ответила:")
    print(ответ)

    папка_назначения = None
    заголовок = None
    for строка in ответ.splitlines():
        строка = строка.strip()
        if строка.upper().startswith("ПАПКА:"):
            папка_назначения = строка.split(":", 1)[1].strip()
        elif строка.upper().startswith("ЗАГОЛОВОК:"):
            заголовок = строка.split(":", 1)[1].strip()

    if not папка_назначения:
        print("Не удалось разобрать ответ модели (нет ПАПКА).")
        return

    if папка_назначения not in папки:
        print(f"Модель предложила папку '{папка_назначения}', которой нет в списке.")
        подтверждение = input("Создать её? (д/н): ").strip().lower()
        if подтверждение != "д":
            print("Отмена.")
            return
        os.makedirs(os.path.join(VAULT, папка_назначения), exist_ok=True)

    старое_имя = os.path.basename(путь_файла).rsplit(".", 1)[0]
    новое_имя = безопасное_имя(заголовок or старое_имя) + ".md"
    новый_путь = os.path.join(VAULT, папка_назначения, новое_имя)

    подтверждение = input(f"\nПоложить в '{папка_назначения}' под именем '{новое_имя}'? (д/н): ").strip().lower()
    if подтверждение != "д":
        print("Отмена.")
        return

    shutil.move(путь_файла, новый_путь)
    print(f"Готово: {новый_путь}")

def разложить_заметку():
    папка_вх = os.path.join(VAULT, ВХОДЯЩИЕ)
    if not os.path.isdir(папка_вх):
        print(f"Нет папки {ВХОДЯЩИЕ}, создай её сначала.")
        return

    файлы = [f for f in os.listdir(папка_вх) if f.endswith(".md")]
    if not файлы:
        print("В папке Входящие нет .md заметок.")
        return

    print("\nЗаметки во Входящих:")
    for i, f in enumerate(файлы, 1):
        print(f"  {i}. {f}")
    выбор = input("Какую разложить? (номер): ").strip()
    if not выбор.isdigit() or not (1 <= int(выбор) <= len(файлы)):
        print("Неверный номер.")
        return
    имя_файла = файлы[int(выбор) - 1]
    путь_файла = os.path.join(папка_вх, имя_файла)
    разложить_конкретную_заметку(путь_файла)

# === АУДИО ===
_whisper_модель = None

def получить_whisper():
    global _whisper_модель
    if _whisper_модель is None:
        print(f"Загружаю модель Whisper ({WHISPER_РАЗМЕР}, {WHISPER_УСТРОЙСТВО})...")
        _whisper_модель = WhisperModel(
            WHISPER_РАЗМЕР,
            device=WHISPER_УСТРОЙСТВО,
            compute_type="int8"
        )
    return _whisper_модель

def обработать_аудио():
    папка_вх = os.path.join(VAULT, ВХОДЯЩИЕ)
    if not os.path.isdir(папка_вх):
        print(f"Нет папки {ВХОДЯЩИЕ}.")
        return

    расширения = ("*.mp3", "*.wav", "*.m4a", "*.ogg", "*.flac", "*.opus", "*.aac")
    файлы = []
    for р in расширения:
        файлы.extend(glob.glob(os.path.join(папка_вх, р)))
    if not файлы:
        print(f"В папке {ВХОДЯЩИЕ} нет аудиофайлов.")
        return

    print("\nАудио во Входящих:")
    for i, f in enumerate(файлы, 1):
        print(f"  {i}. {os.path.basename(f)}")
    выбор = input("Какое обработать? (номер): ").strip()
    if not выбор.isdigit() or not (1 <= int(выбор) <= len(файлы)):
        print("Неверный номер.")
        return

    аудио = файлы[int(выбор) - 1]
    print(f"\nРаспознаю: {os.path.basename(аудио)}")
    модель = получить_whisper()
    сегменты, инфо = модель.transcribe(аудио, language="ru", beam_size=5)
    текст = ""
    for с in сегменты:
        print(с.text, end=" ", flush=True)
        текст += с.text + " "
    текст = текст.strip()
    print()

    if not текст:
        print("Пустой текст, отмена.")
        return

    # Заголовок — первое предложение (до точки), обрезаем до 60 символов
    первое_предложение = текст.split(".")[0][:60].strip()
    заголовок = безопасное_имя(первое_предложение) or "Аудиозаметка"

    новый_файл = os.path.join(папка_вх, заголовок + ".md")
    счётчик = 1
    while os.path.exists(новый_файл):
        новый_файл = os.path.join(папка_вх, f"{заголовок} ({счётчик}).md")
        счётчик += 1

    with open(новый_файл, "w", encoding="utf-8") as f:
        f.write(f"# {заголовок}\n\n{текст}\n")

    print(f"\nЗаметка создана: {os.path.basename(новый_файл)}")

    удалить = input("Удалить исходный аудиофайл? (д/н): ").strip().lower()
    if удалить == "д":
        os.remove(аудио)
        print("Аудио удалено.")

    разложить = input("Разложить заметку по дереву сейчас? (д/н): ").strip().lower()
    if разложить == "д":
        разложить_конкретную_заметку(новый_файл)

# === МЕНЮ ===
def main():
    while True:
        print("\n=== Заметки + ИИ ===")
        print("1. Проверить связь с ИИ")
        print("2. Показать все папки в хранилище")
        print("3. Создать папку")
        print("4. Разложить заметку из Входящих")
        print("5. Обработать аудио из Входящих")
        print("6. Выход")
        choice = input("\nВыбери пункт: ").strip()

        if choice == "1":
            print("Спрашиваю модель, подожди...")
            ответ = спросить_ии("Ответь одним коротким предложением: ты готова работать?")
            print("\nМодель ответила:")
            print(ответ)
        elif choice == "2":
            папки = список_папок()
            if not папки:
                print("В хранилище пока нет папок (кроме Входящих).")
            else:
                print("\nПапки в хранилище:")
                for п in папки:
                    print(f"  - {п}")
        elif choice == "3":
            создать_папку()
        elif choice == "4":
            разложить_заметку()
        elif choice == "5":
            обработать_аудио()
        elif choice == "6":
            print("Выход.")
            sys.exit(0)
        else:
            print("Нет такого пункта.")

if __name__ == "__main__":
    main()