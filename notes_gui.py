import os
import shutil
import threading
import customtkinter as ctk
import ollama
import history
import dialogs
import commands
from faster_whisper import WhisperModel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

VAULT = r"C:\Users\1\Desktop\Tot\Tree"
ВХОДЯЩИЕ = "Входящие"
МОДЕЛЬ_ИИ = "qwen2.5:7b"
WHISPER_РАЗМЕР = "medium"
WHISPER_УСТРОЙСТВО = "cpu"

_whisper_модель = None

def получить_whisper():
    global _whisper_модель
    if _whisper_модель is None:
        _whisper_модель = WhisperModel(
            WHISPER_РАЗМЕР,
            device=WHISPER_УСТРОЙСТВО,
            compute_type="int8"
        )
    return _whisper_модель

def спросить_ии(запрос):
    ответ = ollama.chat(
        model=МОДЕЛЬ_ИИ,
        messages=[{"role": "user", "content": запрос}]
    )
    return ответ["message"]["content"]

def безопасное_имя(текст):
    return "".join(c for c in текст if c not in '\\/:*?"<>|').strip()

# === ФАЙЛОВЫЕ ФУНКЦИИ ===

def список_всех_папок():
    папки = []
    for корень, подпапки, файлы in os.walk(VAULT):
        подпапки[:] = [п for п in подпапки if not п.startswith(".")]
        for п in подпапки:
            полный = os.path.join(корень, п)
            относительный = os.path.relpath(полный, VAULT)
            папки.append(относительный.replace(os.sep, "/"))
    return папки

def список_файлов(относительная_папка):
    полный = os.path.join(VAULT, относительная_папка)
    if not os.path.isdir(полный):
        return []
    return [f for f in os.listdir(полный) if os.path.isfile(os.path.join(полный, f))]

def создать_папку_функция(относительный_путь):
    if not относительный_путь.strip():
        return False, "Пустое имя папки"
    путь = os.path.join(VAULT, относительный_путь)
    try:
        os.makedirs(путь, exist_ok=True)
        return True, f"Папка создана: {относительный_путь}"
    except Exception as e:
        return False, f"Ошибка: {e}"

def перенести_файл_функция(относительный_путь_файла, относительная_папка_назначения):
    источник = os.path.join(VAULT, относительный_путь_файла)
    назначение_папка = os.path.join(VAULT, относительная_папка_назначения)
    if not os.path.isfile(источник):
        return False, f"Файл не найден: {относительный_путь_файла}"
    if not os.path.isdir(назначение_папка):
        return False, f"Папка назначения не найдена: {относительная_папка_назначения}"
    имя = os.path.basename(источник)
    конечный = os.path.join(назначение_папка, имя)
    if os.path.exists(конечный):
        return False, f"В папке назначения уже есть файл с именем {имя}"
    try:
        shutil.move(источник, конечный)
        return True, f"Файл перенесён: {относительный_путь_файла} → {относительная_папка_назначения}"
    except Exception as e:
        return False, f"Ошибка: {e}"

def перенести_папку_функция(относительный_путь_папки, относительный_путь_нового_места):
    источник = os.path.join(VAULT, относительный_путь_папки)
    новое_место = os.path.join(VAULT, относительный_путь_нового_места)
    if not os.path.isdir(источник):
        return False, f"Папка не найдена: {относительный_путь_папки}"
    if not os.path.isdir(новое_место):
        return False, f"Папка назначения не найдена: {относительный_путь_нового_места}"
    источник_абс = os.path.abspath(источник)
    новое_место_абс = os.path.abspath(новое_место)
    if новое_место_абс.startswith(источник_абс + os.sep):
        return False, "Нельзя перенести папку внутрь себя"
    имя = os.path.basename(источник)
    конечный = os.path.join(новое_место, имя)
    if os.path.exists(конечный):
        return False, f"В папке назначения уже есть папка с именем {имя}"
    try:
        shutil.move(источник, конечный)
        return True, f"Папка перенесена: {относительный_путь_папки} → {относительный_путь_нового_места}"
    except Exception as e:
        return False, f"Ошибка: {e}"

# === ГЛАВНОЕ ОКНО ===

class Приложение(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Заметки + ИИ")
        self.geometry("900x600")
        self.minsize(700, 500)

        self.контейнер = ctk.CTkFrame(self, fg_color="transparent")
        self.контейнер.pack(fill="both", expand=True)

        self.текущий_экран = None
        self.показать_экран(ГлавноеМеню)

    def показать_экран(self, класс_экрана):
        if self.текущий_экран is not None:
            self.текущий_экран.destroy()
        self.текущий_экран = класс_экрана(self.контейнер, self)
        self.текущий_экран.pack(fill="both", expand=True)

    def кнопка_главное_меню(self, родитель):
        return ctk.CTkButton(
            родитель,
            text="← Главное меню",
            width=160,
            command=lambda: self.показать_экран(ГлавноеМеню)
        )

# === ЭКРАНЫ ===

class ГлавноеМеню(ctk.CTkFrame):
    def __init__(self, родитель, приложение):
        super().__init__(родитель, fg_color="transparent")
        self.приложение = приложение

        ctk.CTkLabel(self, text="Заметки + ИИ", font=("", 24, "bold")).pack(pady=(40, 30))

        кнопки = [
            ("Работа с файлами", РаботаСФайлами),
            ("Расшифровка аудио", РасшифровкаАудио),
            ("Истории", ЭкранИсторий),
            ("Выход", None),
        ]
        for текст, экран in кнопки:
            if экран is None:
                команда = self.приложение.destroy
            else:
                команда = lambda э=экран: self.приложение.показать_экран(э)
            ctk.CTkButton(
                self, text=текст, width=300, height=45, font=("", 15),
                command=команда
            ).pack(pady=8)


class РаботаСФайлами(ctk.CTkFrame):
    def __init__(self, родитель, приложение):
        super().__init__(родитель, fg_color="transparent")
        self.приложение = приложение

        self.приложение.кнопка_главное_меню(self).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self, text="Работа с файлами", font=("", 20, "bold")).pack(pady=(10, 20))

        ctk.CTkButton(self, text="Перенести файл", width=280, height=40,
                      command=self.открыть_перенос_файла).pack(pady=6)
        ctk.CTkButton(self, text="Создать папку", width=280, height=40,
                      command=self.открыть_создание_папки).pack(pady=6)
        ctk.CTkButton(self, text="Перенести папку", width=280, height=40,
                      command=self.открыть_перенос_папки).pack(pady=6)

    def открыть_перенос_файла(self):
        ОкноПереносаФайла(self).grab_set()

    def открыть_создание_папки(self):
        ОкноСозданияПапки(self).grab_set()

    def открыть_перенос_папки(self):
        ОкноПереносаПапки(self).grab_set()


class ОкноПереносаФайла(ctk.CTkToplevel):
    def __init__(self, родитель):
        super().__init__(родитель)
        self.title("Перенести файл")
        self.geometry("600x500")

        self.папки = список_всех_папок()

        ctk.CTkLabel(self, text="1. Откуда (папка-источник):", anchor="w").pack(fill="x", padx=15, pady=(15, 3))
        self.выбор_источника = ctk.CTkOptionMenu(self, values=self.папки,
                                                 command=self.обновить_файлы, width=400)
        self.выбор_источника.pack(padx=15, pady=3)

        ctk.CTkLabel(self, text="2. Какой файл:", anchor="w").pack(fill="x", padx=15, pady=(15, 3))
        self.выбор_файла = ctk.CTkOptionMenu(self, values=["—"], width=400)
        self.выбор_файла.pack(padx=15, pady=3)

        ctk.CTkLabel(self, text="3. Куда (папка-назначение):", anchor="w").pack(fill="x", padx=15, pady=(15, 3))
        self.выбор_назначения = ctk.CTkOptionMenu(self, values=self.папки, width=400)
        self.выбор_назначения.pack(padx=15, pady=3)

        self.результат = ctk.CTkLabel(self, text="", wraplength=560, justify="left")
        self.результат.pack(padx=15, pady=15)

        ctk.CTkButton(self, text="Перенести", command=self.выполнить).pack(pady=5)
        ctk.CTkButton(self, text="Отмена", command=self.destroy, fg_color="gray").pack(pady=5)

        if self.папки:
            self.выбор_источника.set(self.папки[0])
            self.обновить_файлы(self.папки[0])
            self.выбор_назначения.set(self.папки[0])

    def обновить_файлы(self, папка):
        файлы = список_файлов(папка)
        if файлы:
            self.выбор_файла.configure(values=файлы)
            self.выбор_файла.set(файлы[0])
        else:
            self.выбор_файла.configure(values=["— нет файлов —"])
            self.выбор_файла.set("— нет файлов —")

    def выполнить(self):
        источник_папка = self.выбор_источника.get()
        имя_файла = self.выбор_файла.get()
        назначение = self.выбор_назначения.get()
        if имя_файла.startswith("—"):
            self.результат.configure(text="Нет файла для переноса.")
            return
        относительный_путь = f"{источник_папка}/{имя_файла}"
        ok, сообщение = перенести_файл_функция(относительный_путь, назначение)
        self.результат.configure(text=сообщение)
        if ok:
            self.обновить_файлы(источник_папка)


class ОкноСозданияПапки(ctk.CTkToplevel):
    def __init__(self, родитель):
        super().__init__(родитель)
        self.title("Создать папку")
        self.geometry("500x250")

        ctk.CTkLabel(self, text="Имя новой папки.\nМожно вложенную через слэш: Проекты/Идеи",
                     justify="left").pack(padx=15, pady=(20, 10), anchor="w")
        self.ввод = ctk.CTkEntry(self, width=400)
        self.ввод.pack(padx=15, pady=5)
        self.результат = ctk.CTkLabel(self, text="", wraplength=460, justify="left")
        self.результат.pack(padx=15, pady=10)

        ctk.CTkButton(self, text="Создать", command=self.выполнить).pack(pady=5)
        ctk.CTkButton(self, text="Отмена", command=self.destroy, fg_color="gray").pack(pady=5)

    def выполнить(self):
        имя = self.ввод.get().strip()
        ok, сообщение = создать_папку_функция(имя)
        self.результат.configure(text=сообщение)
        if ok:
            self.ввод.delete(0, "end")


class ОкноПереносаПапки(ctk.CTkToplevel):
    def __init__(self, родитель):
        super().__init__(родитель)
        self.title("Перенести папку")
        self.geometry("600x350")

        self.папки = список_всех_папок()

        ctk.CTkLabel(self, text="1. Какую папку перенести:", anchor="w").pack(fill="x", padx=15, pady=(15, 3))
        self.выбор_папки = ctk.CTkOptionMenu(self, values=self.папки, width=400)
        self.выбор_папки.pack(padx=15, pady=3)

        ctk.CTkLabel(self, text="2. Куда перенести (внутрь какой папки):", anchor="w").pack(fill="x", padx=15, pady=(15, 3))
        self.выбор_назначения = ctk.CTkOptionMenu(self, values=self.папки, width=400)
        self.выбор_назначения.pack(padx=15, pady=3)

        self.результат = ctk.CTkLabel(self, text="", wraplength=560, justify="left")
        self.результат.pack(padx=15, pady=15)

        ctk.CTkButton(self, text="Перенести", command=self.выполнить).pack(pady=5)
        ctk.CTkButton(self, text="Отмена", command=self.destroy, fg_color="gray").pack(pady=5)

        if self.папки:
            self.выбор_папки.set(self.папки[0])
            self.выбор_назначения.set(self.папки[0])

    def выполнить(self):
        папка = self.выбор_папки.get()
        назначение = self.выбор_назначения.get()
        ok, сообщение = перенести_папку_функция(папка, назначение)
        self.результат.configure(text=сообщение)


class РасшифровкаАудио(ctk.CTkFrame):
    def __init__(self, родитель, приложение):
        super().__init__(родитель, fg_color="transparent")
        self.приложение = приложение
        self.переименованные_аудио = []
        self.идёт_работа = False

        self.приложение.кнопка_главное_меню(self).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self, text="Расшифровка аудио", font=("", 20, "bold")).pack(pady=(10, 10))

        self.список_фрейм = ctk.CTkScrollableFrame(self, width=700, height=320)
        self.список_фрейм.pack(padx=20, pady=10, fill="both", expand=True)

        self.кнопки_фрейм = ctk.CTkFrame(self, fg_color="transparent")
        self.кнопки_фрейм.pack(pady=10)

        ctk.CTkButton(self.кнопки_фрейм, text="Расшифровать всё", width=180,
                      command=lambda: self.запустить([])).pack(side="left", padx=5)
        ctk.CTkButton(self.кнопки_фрейм, text="Выбрать и расшифровать", width=200,
                      command=self.выбрать_и_запустить).pack(side="left", padx=5)

        # Прогресс-бар, скрыт по умолчанию
        self.прогресс_фрейм = ctk.CTkFrame(self, fg_color="transparent")
        self.прогресс_текст = ctk.CTkLabel(self.прогресс_фрейм, text="", font=("", 12))
        self.прогресс_текст.pack(pady=(0, 5))
        self.прогресс_бар = ctk.CTkProgressBar(self.прогресс_фрейм, width=500)
        self.прогресс_бар.set(0)
        self.прогресс_бар.pack()

        self.галочки = {}
        self.обновить_список()

    def обновить_список(self):
        for виджет in self.список_фрейм.winfo_children():
            виджет.destroy()
        self.галочки.clear()

        аудио_папка = os.path.join(VAULT, ВХОДЯЩИЕ)
        if not os.path.isdir(аудио_папка):
            ctk.CTkLabel(self.список_фрейм, text=f"Папка {ВХОДЯЩИЕ} не найдена.").pack(pady=20)
            return

        расширения = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".opus", ".aac")
        файлы = sorted(f for f in os.listdir(аудио_папка) if f.lower().endswith(расширения))

        if not файлы:
            ctk.CTkLabel(self.список_фрейм, text=f"В папке {ВХОДЯЩИЕ} нет аудиофайлов.").pack(pady=20)
            return

        ctk.CTkLabel(self.список_фрейм, text=f"Найдено аудио: {len(файлы)}", font=("", 13)).pack(anchor="w", padx=10, pady=(5, 10))

        for имя in файлы:
            var = ctk.BooleanVar(value=False)
            self.галочки[имя] = var
            ctk.CTkCheckBox(self.список_фрейм, text=имя, variable=var).pack(anchor="w", padx=10, pady=3)

    def выбрать_и_запустить(self):
        отмеченные = [имя for имя, var in self.галочки.items() if var.get()]
        if not отмеченные:
            print("[инфо] Ничего не отмечено")
            return
        self.запустить(отмеченные)

    def запустить(self, список_файлов):
        if self.идёт_работа:
            print("[инфо] Уже идёт расшифровка")
            return

        if not список_файлов:
            список_файлов = list(self.галочки.keys())
        if not список_файлов:
            print("[инфо] Нет файлов для обработки")
            return

        self.идёт_работа = True
        self.кнопки_фрейм.pack_forget()
        self.прогресс_фрейм.pack(pady=10)

        поток = threading.Thread(
            target=self._работать_в_потоке,
            args=(список_файлов,),
            daemon=True
        )
        поток.start()

    def _работать_в_потоке(self, список_файлов):
        результаты = []
        ошибки = []
        переименованные_аудио = []
        папка_вх = os.path.join(VAULT, ВХОДЯЩИЕ)
        папки = список_всех_папок()
        всего = len(список_файлов)

        for индекс, имя_файла in enumerate(список_файлов, start=1):
            self.обновить_прогресс(индекс, всего, имя_файла)
            путь = os.path.join(папка_вх, имя_файла)
            print(f"\n=== Обрабатываю: {имя_файла} ===")

            try:
                модель = получить_whisper()
                сегменты, инфо = модель.transcribe(путь, language="ru", beam_size=5)
                текст = " ".join(с.text for с in сегменты).strip()
            except Exception as e:
                print(f"  Ошибка распознавания: {e}")
                ошибки.append((имя_файла, f"распознавание: {e}"))
                continue

            if not текст:
                print("  Пустой текст, пропускаю.")
                ошибки.append((имя_файла, "пустой текст"))
                continue
            # Проверяем, не команда ли это
            if commands.найти_триггер(текст) is not None:
                print(f"  Это команда: {текст}")
                результаты_команд = commands.обработать_текст(текст)

                if not результаты_команд:
                    # Триггер есть, но команд не извлеклось —
                    # отправляем весь текст в чат с Филином и удаляем аудио
                    ошибки.append((имя_файла, "триггер есть, команд нет"))
                    текст_для_диалога = текст
                    слова = текст_для_диалога.split()
                    for i in range(min(3, len(слова))):
                        if слова[i].lower().strip(".,!?:;-—–\"'«»") == "филин":
                            текст_для_диалога = " ".join(слова[i + 1:]).strip()
                            break
                    имя_чата = dialogs.создать_чат(текст_для_диалога or "(пустая команда)")
                    try:
                        сообщения_для_ии = dialogs.сообщения_для_ии(имя_чата)
                        ответ = ollama.chat(model=МОДЕЛЬ_ИИ, messages=сообщения_для_ии)
                        dialogs.добавить_сообщение(имя_чата, "assistant",
                                                   ответ["message"]["content"])
                    except Exception as e:
                        dialogs.добавить_сообщение(имя_чата, "assistant", f"[ошибка ИИ: {e}]")
                    try:
                        os.remove(путь)
                        print(f"  Командное аудио удалено: {имя_файла}")
                    except Exception as e:
                        print(f"  Ошибка удаления: {e}")
                    continue

                хотя_бы_одна_распознана = any(была for _, _, была in результаты_команд)
                хотя_бы_одна_успешна = any(ok for ok, _, _ in результаты_команд)

                if не_распознано := not хотя_бы_одна_распознана:
                    # Ни одна команда не распознана — отправляем в диалог с Филином
                    текст_для_диалога = команда_для_диалога = текст
                    # Убираем 'Филин' в начале, если он есть в первых словах
                    слова = текст_для_диалога.split()
                    for i in range(min(3, len(слова))):
                        if слова[i].lower().strip(".,!?:;-—–\"'«»") == "филин":
                            текст_для_диалога = " ".join(слова[i + 1:]).strip()
                            break

                    имя_чата = dialogs.создать_чат(текст_для_диалога)
                    try:
                        сообщения_для_ии = dialogs.сообщения_для_ии(имя_чата)
                        ответ = ollama.chat(model=МОДЕЛЬ_ИИ, messages=сообщения_для_ии)
                        dialogs.добавить_сообщение(имя_чата, "assistant",
                                                   ответ["message"]["content"])
                    except Exception as e:
                        dialogs.добавить_сообщение(имя_чата, "assistant", f"[ошибка ИИ: {e}]")
                    print(f"  Команда не распознана, создан чат: {имя_чата}")

                # Аудио команд сразу удаляем — оно уже сделало своё дело
                try:
                    os.remove(путь)
                    print(f"  Командное аудио удалено: {имя_файла}")
                except Exception as e:
                    print(f"  Ошибка удаления командного аудио: {e}")
                continue              

            промт = f"""Ты — помощник по сортировке заметок.
Вот список существующих папок:
{chr(10).join('- ' + p for p in папки)}

Вот текст голосовой заметки:
\"\"\"
{текст}
\"\"\"

Придумай короткое название для этой заметки (3–7 слов) и выбери, в какую папку её положить.
Ответь СТРОГО в формате:
НАЗВАНИЕ: <короткое название>
ПАПКА: <название папки из списка>
"""
            try:
                ответ = спросить_ии(промт)
            except Exception as e:
                print(f"  Ошибка ИИ: {e}")
                ошибки.append((имя_файла, f"ИИ: {e}"))
                continue

            новое_название = None
            папка = None
            for строка in ответ.splitlines():
                строка = строка.strip()
                if строка.upper().startswith("НАЗВАНИЕ:"):
                    новое_название = строка.split(":", 1)[1].strip()
                elif строка.upper().startswith("ПАПКА:"):
                    папка = строка.split(":", 1)[1].strip()

            if not новое_название or not папка:
                print(f"  Не удалось разобрать ответ ИИ: {ответ}")
                ошибки.append((имя_файла, "ответ ИИ не по формату"))
                continue

            новое_название = безопасное_имя(новое_название) or "Без названия"

            расширение = os.path.splitext(имя_файла)[1]
            новое_аудио_имя = новое_название + расширение
            новый_аудио_путь = os.path.join(папка_вх, новое_аудио_имя)
            счётчик = 1
            while os.path.exists(новый_аудио_путь):
                новое_аудио_имя = f"{новое_название} ({счётчик}){расширение}"
                новый_аудио_путь = os.path.join(папка_вх, новое_аудио_имя)
                счётчик += 1
            os.rename(путь, новый_аудио_путь)
            переименованные_аудио.append(новое_аудио_имя)

            новое_имя_заметки = новое_название + ".md"
            путь_заметки = os.path.join(папка_вх, новое_имя_заметки)
            счётчик = 1
            while os.path.exists(путь_заметки):
                новое_имя_заметки = f"{новое_название} ({счётчик}).md"
                путь_заметки = os.path.join(папка_вх, новое_имя_заметки)
                счётчик += 1

            with open(путь_заметки, "w", encoding="utf-8") as f:
                f.write(f"# {новое_название}\n\n{текст}\n")

            результаты.append({
                "заметка": новое_имя_заметки,
                "название": новое_название,
                "папка_предложение": папка,
            })

        # Возвращаемся в главный поток
        self.after(0, lambda: self._завершить(результаты, ошибки, переименованные_аудио, папки))

    def обновить_прогресс(self, номер, всего, имя):
        def _обновить():
            self.прогресс_текст.configure(text=f"Обрабатываю {номер} из {всего}: {имя}")
            self.прогресс_бар.set(номер / всего)
        self.after(0, _обновить)

    def _завершить(self, результаты, ошибки, переименованные_аудио, папки):
        self.идёт_работа = False
        self.прогресс_фрейм.pack_forget()
        self.кнопки_фрейм.pack(pady=10)
        self.обновить_список()

        if ошибки:
            ОкноОшибок(self, ошибки).grab_set()

        if not результаты:
            print("\n[инфо] Ничего не расшифровано.")
            return

        self.переименованные_аудио = переименованные_аудио
    def _завершить(self, результаты, ошибки, переименованные_аудио, папки):
        self.идёт_работа = False
        self.прогресс_фрейм.pack_forget()
        self.кнопки_фрейм.pack(pady=10)
        self.обновить_список()

        # Если были только команды (без обычных заметок) —
        # открываем сразу окно удаления аудио.
        if not результаты:
            self.переименованные_аудио = переименованные_аудио
            if переименованные_аудио:
                ОкноУдаленияАудио(
                    self.master,
                    переименованные_аудио,
                    self.приложение,
                ).grab_set()
            else:
                print("\n[инфо] Ничего не расшифровано.")
            return

        self.переименованные_аудио = переименованные_аудио
        ОкноРаскладки(
            self,
            результаты,
            папки,
            переименованные_аудио,
            self.приложение,
        ).grab_set()


class ЭкранИсторий(ctk.CTkFrame):
    def __init__(self, родитель, приложение):
        super().__init__(родитель, fg_color="transparent")
        self.приложение = приложение

        self.приложение.кнопка_главное_меню(self).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self, text="Истории", font=("", 20, "bold")).pack(pady=(10, 5))

        self.вкладки = ctk.CTkTabview(self, width=850, height=470)
        self.вкладки.pack(padx=20, pady=10, fill="both", expand=True)

        self.вкладки.add("Диалог с Филином")
        self.вкладки.add("Действия ИИ")
        self.вкладки.add("Прочее")

        self.вкладки.set("Диалог с Филином")

        self._собрать_диалог()
        self._собрать_действия()
        self._собрать_прочее()

    # === ДИАЛОГ С ФИЛИНОМ ===
    def _собрать_диалог(self):
        вкладка = self.вкладки.tab("Диалог с Филином")

        верх = ctk.CTkFrame(вкладка, fg_color="transparent")
        верх.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(верх, text="Кликни на чат — он откроется в отдельном окне.",
                     font=("", 12), text_color="#909090").pack(side="left")
        ctk.CTkButton(верх, text="Обновить", width=120, command=self._обновить_чаты).pack(side="right")

        self.список_чатов_фрейм = ctk.CTkScrollableFrame(вкладка)
        self.список_чатов_фрейм.pack(fill="both", expand=True, padx=10, pady=5)

        self._обновить_чаты()

    def _обновить_чаты(self):
        for виджет in self.список_чатов_фрейм.winfo_children():
            виджет.destroy()

        чаты = dialogs.список_чатов()
        if not чаты:
            ctk.CTkLabel(self.список_чатов_фрейм, text="Чатов нет.").pack(pady=10)
            return

        for ч in чаты:
            текст = ч["заголовок"] or "(без заголовка)"
            метка = "✓ " if ч["завершён"] else ""
            кнопка = ctk.CTkButton(
                self.список_чатов_фрейм,
                text=f"{метка}{текст}  ·  {ч['создан']}  ·  сообщений: {ч['сообщений']}",
                anchor="w",
                height=36,
                fg_color="#2a2a2a" if ч["завершён"] else None,
                command=lambda иф=ч["имя_файла"]: self._открыть_чат(иф)
            )
            кнопка.pack(fill="x", pady=3)

    def _открыть_чат(self, имя_файла):
        окно = ОкноЧата(self, имя_файла)
        окно.after(100, lambda: окно.lift())   # поднять над всеми окнами приложения
        окно.after(100, lambda: окно.focus())

    # === ДЕЙСТВИЯ ИИ ===
    def _собрать_действия(self):
        вкладка = self.вкладки.tab("Действия ИИ")
        self.фрейм_действий = ctk.CTkScrollableFrame(вкладка)
        self.фрейм_действий.pack(fill="both", expand=True, padx=5, pady=5)

        кнопки = ctk.CTkFrame(вкладка, fg_color="transparent")
        кнопки.pack(pady=5)
        ctk.CTkButton(кнопки, text="Обновить", width=120, command=self._обновить_действия).pack(side="left", padx=5)
        ctk.CTkButton(кнопки, text="Очистить", width=120, fg_color="#b03030",
                      hover_color="#8b2020", command=self._очистить_действия).pack(side="left", padx=5)

        self._обновить_действия()

    def _обновить_действия(self):
        for виджет in self.фрейм_действий.winfo_children():
            виджет.destroy()
        записи = history.прочитать_действия(последних=50)
        if not записи:
            ctk.CTkLabel(self.фрейм_действий, text="Записей нет.").pack(pady=20)
            return
        for запись in записи:
            self._добавить_строку(self.фрейм_действий, запись)

    def _очистить_действия(self):
        history.очистить_действия()
        self._обновить_действия()

    # === ПРОЧЕЕ ===
    def _собрать_прочее(self):
        вкладка = self.вкладки.tab("Прочее")
        self.фрейм_прочего = ctk.CTkScrollableFrame(вкладка)
        self.фрейм_прочего.pack(fill="both", expand=True, padx=5, pady=5)

        кнопки = ctk.CTkFrame(вкладка, fg_color="transparent")
        кнопки.pack(pady=5)
        ctk.CTkButton(кнопки, text="Обновить", width=120, command=self._обновить_прочее).pack(side="left", padx=5)
        ctk.CTkButton(кнопки, text="Очистить", width=120, fg_color="#b03030",
                      hover_color="#8b2020", command=self._очистить_прочее).pack(side="left", padx=5)

        self._обновить_прочее()

    def _обновить_прочее(self):
        for виджет in self.фрейм_прочего.winfo_children():
            виджет.destroy()
        записи = history.прочитать_прочее(последних=50)
        if not записи:
            ctk.CTkLabel(self.фрейм_прочего, text="Записей нет.").pack(pady=20)
            return
        for запись in записи:
            self._добавить_строку(self.фрейм_прочего, запись)

    def _очистить_прочее(self):
        history.очистить_прочее()
        self._обновить_прочее()

    # === ОБЩЕЕ ===
    def _добавить_строку(self, родитель, запись):
        строка = ctk.CTkFrame(родитель, fg_color="transparent")
        строка.pack(fill="x", pady=2)
        ctk.CTkLabel(строка, text=запись["время"], width=150, anchor="w",
                     text_color="#909090").pack(side="left", padx=(5, 10))
        ctk.CTkLabel(строка, text=запись["текст"], anchor="w", justify="left",
                     wraplength=550).pack(side="left", fill="x", expand=True)


class ОкноЧата(ctk.CTkToplevel):
    def __init__(self, родитель, имя_файла):
        super().__init__()
        self.имя_файла = имя_файла
        self.родитель_экран = родитель
        self.ожидание = False

        данные = dialogs.прочитать_чат(имя_файла)
        if данные is None:
            self.destroy()
            return

        заголовок = данные.get("сообщения", [{}])[0].get("текст", "")[:50] if данные.get("сообщения") else "Чат"
        self.title(f"Филин · {заголовок}")
        self.geometry("650x600")
        self.minsize(500, 400)

        # Верхняя строка с заголовком и статусом
        верх = ctk.CTkFrame(self, fg_color="transparent")
        верх.pack(fill="x", padx=10, pady=(10, 5))
        self.статус_метка = ctk.CTkLabel(верх, text="", font=("", 11), text_color="#909090")
        self.статус_метка.pack(side="left")

        # Лента
        self.лента = ctk.CTkScrollableFrame(self)
        self.лента.pack(fill="both", expand=True, padx=10, pady=5)

        # Низ — ввод и кнопки
        низ = ctk.CTkFrame(self, fg_color="transparent")
        низ.pack(fill="x", padx=10, pady=(5, 10))
        self.ввод = ctk.CTkEntry(низ, placeholder_text="Напиши ответ...")
        self.ввод.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.ввод.bind("<Return>", lambda e: self._отправить())
        self.кнопка_отправить = ctk.CTkButton(низ, text="Отправить", width=100,
                                              command=self._отправить)
        self.кнопка_отправить.pack(side="left")
        ctk.CTkButton(низ, text="Завершить", width=100, fg_color="gray",
                      command=self._завершить).pack(side="left", padx=(5, 0))

        self._перерисовать()
        self.after(100, self.ввод.focus)

    def _перерисовать(self):
        for виджет in self.лента.winfo_children():
            виджет.destroy()
        данные = dialogs.прочитать_чат(self.имя_файла)
        if данные is None:
            return
        for м in данные.get("сообщения", []):
            роль = "Ты" if м.get("роль") == "user" else "Филин"
            цвет = "#3a5a8a" if м.get("роль") == "user" else "#3a3a3a"
            блок = ctk.CTkFrame(self.лента, fg_color=цвет, corner_radius=8)
            блок.pack(fill="x", pady=4, padx=5)
            ctk.CTkLabel(блок, text=f"{роль} · {м.get('время', '')}",
                         font=("", 10), text_color="#c0c0c0").pack(anchor="w", padx=8, pady=(5, 2))
            ctk.CTkLabel(блок, text=м.get("текст", ""), anchor="w",
                         justify="left", wraplength=520).pack(anchor="w", padx=8, pady=(0, 6))
        # Прокрутить в самый низ
        self.лента.update_idletasks()
        try:
            self.лента._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass                         

    def _отправить(self):
        if self.ожидание:
            return
        текст = self.ввод.get().strip()
        if not текст:
            return
        self.ввод.delete(0, "end")

        dialogs.добавить_сообщение(self.имя_файла, "user", текст)
        self._перерисовать()
        self._запустить_ответ_ии()

    def _запустить_ответ_ии(self):
        self.ожидание = True
        self.кнопка_отправить.configure(state="disabled")
        self.статус_метка.configure(text="Филин думает...")

        поток = threading.Thread(target=self._получить_ответ, daemon=True)
        поток.start()

    def _получить_ответ(self):
        try:
            сообщения = dialogs.сообщения_для_ии(self.имя_файла)
            ответ = ollama.chat(model=МОДЕЛЬ_ИИ, messages=сообщения)
            текст_ответа = ответ["message"]["content"]
            dialogs.добавить_сообщение(self.имя_файла, "assistant", текст_ответа)
        except Exception as e:
            dialogs.добавить_сообщение(self.имя_файла, "assistant", f"[ошибка ИИ: {e}]")

        # Возвращаемся в главный поток, чтобы обновить интерфейс
        self.after(0, self._завершить_ответ)

    def _завершить_ответ(self):
        self.ожидание = False
        self.кнопка_отправить.configure(state="normal")
        self.статус_метка.configure(text="")
        self._перерисовать()

    def _завершить(self):
        dialogs.завершить_чат(self.имя_файла)
        self.destroy()


class ОкноОшибок(ctk.CTkToplevel):
    def __init__(self, родитель, ошибки):
        super().__init__(родитель)
        self.title("Не удалось обработать")
        self.geometry("600x400")

        ctk.CTkLabel(
            self,
            text=f"Проблемных файлов: {len(ошибки)}.\nОни остались во Входящих.",
            font=("", 14, "bold"), justify="center"
        ).pack(pady=(15, 10))

        фрейм = ctk.CTkScrollableFrame(self, width=560, height=250)
        фрейм.pack(padx=15, pady=10, fill="both", expand=True)

        for имя, причина in ошибки:
            строка = ctk.CTkFrame(фрейм, fg_color="transparent")
            строка.pack(fill="x", pady=3)
            ctk.CTkLabel(строка, text=имя, anchor="w", width=250).pack(side="left", padx=5)
            ctk.CTkLabel(строка, text=причина, anchor="w", text_color="#e08080").pack(side="left", padx=5)

        ctk.CTkButton(self, text="Понятно", command=self.destroy).pack(pady=10)


class ОкноРаскладки(ctk.CTkToplevel):
    def __init__(self, родитель, результаты, папки, переименованные_аудио, приложение):
        super().__init__(родитель)
        self.title("Куда разложить")
        self.geometry("800x600")
        self.папки = папки
        self.результаты = результаты
        self.выборы = {}
        self.переименованные_аудио = переименованные_аудио
        self.приложение = приложение

        ctk.CTkLabel(self, text="Проверь, куда положить каждую заметку",
                     font=("", 16, "bold")).pack(pady=(15, 10))

        фрейм = ctk.CTkScrollableFrame(self, width=760, height=440)
        фрейм.pack(padx=15, pady=5, fill="both", expand=True)

        варианты = папки + ["Временное"]

        for рез in результаты:
            строка = ctk.CTkFrame(фрейм, fg_color="transparent")
            строка.pack(fill="x", pady=4)
            ctk.CTkLabel(строка, text=рез["название"], width=350, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(строка, text="→").pack(side="left", padx=5)
            var = ctk.StringVar(value=рез["папка_предложение"])
            self.выборы[рез["заметка"]] = var
            ctk.CTkOptionMenu(строка, values=варианты, variable=var, width=200).pack(side="left", padx=5)

        кнопки = ctk.CTkFrame(self, fg_color="transparent")
        кнопки.pack(pady=10)
        ctk.CTkButton(кнопки, text="Применить всё", width=180, command=self.применить).pack(side="left", padx=5)
        ctk.CTkButton(кнопки, text="Отмена", width=120, fg_color="gray", command=self.destroy).pack(side="left", padx=5)

    def применить(self):
        папка_вх = os.path.join(VAULT, ВХОДЯЩИЕ)
        for рез in self.результаты:
            папка = self.выборы[рез["заметка"]].get()
            источник = os.path.join(папка_вх, рез["заметка"])
            назначение_папка = os.path.join(VAULT, папка)
            os.makedirs(назначение_папка, exist_ok=True)
            назначение = os.path.join(назначение_папка, рез["заметка"])
            try:
                shutil.move(источник, назначение)
                print(f"Перенесено: {рез['заметка']} → {папка}")
            except Exception as e:
                print(f"Ошибка переноса {рез['заметка']}: {e}")

        self.destroy()
        ОкноУдаленияАудио(
            self.master,
            self.переименованные_аудио,
            self.приложение,
        ).grab_set()


class ОкноУдаленияАудио(ctk.CTkToplevel):
    def __init__(self, родитель, список_аудио, приложение):
        super().__init__(родитель)
        self.приложение = приложение
        self.title("Удалить аудио?")
        self.geometry("700x500")

        ctk.CTkLabel(
            self,
            text="Аудио расшифрованы.\nУдали ненужные — остальные уедут в «Временное аудио».",
            font=("", 15, "bold"), justify="center"
        ).pack(pady=(15, 10))

        self.список_фрейм = ctk.CTkScrollableFrame(self, width=660, height=300)
        self.список_фрейм.pack(padx=15, pady=10, fill="both", expand=True)

        папка_вх = os.path.join(VAULT, ВХОДЯЩИЕ)
        self.аудио = [
            имя for имя in список_аудио
            if os.path.isfile(os.path.join(папка_вх, имя))
        ]

        self.галочки = {}
        if not self.аудио:
            ctk.CTkLabel(self.список_фрейм, text="Аудиофайлов для удаления нет.").pack(pady=20)
        else:
            for имя in self.аудио:
                var = ctk.BooleanVar(value=False)
                self.галочки[имя] = var
                ctk.CTkCheckBox(self.список_фрейм, text=имя, variable=var).pack(anchor="w", padx=10, pady=3)

        кнопки = ctk.CTkFrame(self, fg_color="transparent")
        кнопки.pack(pady=10)

        ctk.CTkButton(кнопки, text="Удалить всё", width=160, fg_color="#b03030",
                      hover_color="#8b2020", command=self.удалить_всё).pack(side="left", padx=5)
        ctk.CTkButton(кнопки, text="Удалить отмеченные", width=180, fg_color="#b03030",
                      hover_color="#8b2020", command=self.удалить_отмеченные).pack(side="left", padx=5)
        ctk.CTkButton(кнопки, text="Отмена", width=120, fg_color="gray",
                      command=self.отмена).pack(side="left", padx=5)

    def перенести_во_временное(self, список):
        источник_папка = os.path.join(VAULT, ВХОДЯЩИЕ)
        цель_папка = os.path.join(VAULT, "Временное аудио")
        os.makedirs(цель_папка, exist_ok=True)
        for имя in список:
            источник = os.path.join(источник_папка, имя)
            назначение = os.path.join(цель_папка, имя)
            счётчик = 1
            базовое, расширение = os.path.splitext(имя)
            while os.path.exists(назначение):
                назначение = os.path.join(цель_папка, f"{базовое} ({счётчик}){расширение}")
                счётчик += 1
            try:
                shutil.move(источник, назначение)
                print(f"Во временное: {имя}")
            except Exception as e:
                print(f"Ошибка переноса {имя}: {e}")

    def удалить_файлы(self, на_удаление):
        папка_вх = os.path.join(VAULT, ВХОДЯЩИЕ)
        for имя in на_удаление:
            путь = os.path.join(папка_вх, имя)
            try:
                os.remove(путь)
                print(f"Удалено: {имя}")
            except Exception as e:
                print(f"Ошибка удаления {имя}: {e}")

        остальные = [и for и in self.аудио if и not in на_удаление]
        if остальные:
            self.перенести_во_временное(остальные)

        self.destroy()
        self.приложение.показать_экран(ГлавноеМеню)

    def удалить_всё(self):
        self.удалить_файлы(self.аудио)

    def удалить_отмеченные(self):
        отмеченные = [имя for имя, var in self.галочки.items() if var.get()]
        if not отмеченные:
            print("[инфо] Ничего не отмечено, переношу всё во временное.")
            self.перенести_во_временное(self.аудио)
            self.destroy()
            self.приложение.показать_экран(ГлавноеМеню)
            return
        self.удалить_файлы(отмеченные)

    def отмена(self):
        self.перенести_во_временное(self.аудио)
        self.destroy()
        self.приложение.показать_экран(ГлавноеМеню)


if __name__ == "__main__":
    app = Приложение()
    app.mainloop()