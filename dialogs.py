import os
import json
from datetime import datetime

DATA_DIR = r"C:\Users\1\Desktop\Tot\Ai\data"
DIALOGS_DIR = os.path.join(DATA_DIR, "dialogs")


def _путь_чата(имя_файла):
    return os.path.join(DIALOGS_DIR, имя_файла)


def _загрузить(имя_файла):
    путь = _путь_чата(имя_файла)
    if not os.path.isfile(путь):
        return None
    try:
        with open(путь, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _сохранить(имя_файла, данные):
    os.makedirs(DIALOGS_DIR, exist_ok=True)
    путь = _путь_чата(имя_файла)
    with open(путь, "w", encoding="utf-8") as f:
        json.dump(данные, f, ensure_ascii=False, indent=2)


def создать_чат(первая_реплика):
    """Создаёт новый чат с первой репликой пользователя.
    Возвращает имя файла чата."""
    время = datetime.now()
    имя_файла = время.strftime("%Y-%m-%d_%H-%M-%S") + ".json"
    данные = {
        "создан": время.strftime("%Y-%m-%d %H:%M:%S"),
        "завершён": False,
        "сообщения": [
            {
                "роль": "user",
                "время": время.strftime("%Y-%m-%d %H:%M:%S"),
                "текст": первая_реплика.strip()
            }
        ]
    }
    _сохранить(имя_файла, данные)
    return имя_файла


def добавить_сообщение(имя_файла, роль, текст):
    """Добавляет сообщение в чат.
    роль: 'user' или 'assistant'."""
    данные = _загрузить(имя_файла)
    if данные is None:
        return False
    данные["сообщения"].append({
        "роль": роль,
        "время": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "текст": текст.strip()
    })
    _сохранить(имя_файла, данные)
    return True


def завершить_чат(имя_файла):
    данные = _загрузить(имя_файла)
    if данные is None:
        return False
    данные["завершён"] = True
    _сохранить(имя_файла, данные)
    return True


def удалить_чат(имя_файла):
    путь = _путь_чата(имя_файла)
    if os.path.isfile(путь):
        os.remove(путь)
        return True
    return False


def список_чатов():
    """Возвращает список чатов, отсортированный:
    сначала активные (свежие сверху), потом завершённые (свежие сверху).
    Каждый элемент: {"имя_файла": ..., "создан": ..., "завершён": ...,
                     "заголовок": ..., "сообщений": N}"""
    if not os.path.isdir(DIALOGS_DIR):
        return []

    чаты = []
    for имя_файла in os.listdir(DIALOGS_DIR):
        if not имя_файла.endswith(".json"):
            continue
        данные = _загрузить(имя_файла)
        if данные is None:
            continue
        сообщения = данные.get("сообщения", [])
        заголовок = ""
        for м in сообщения:
            if м.get("роль") == "user":
                заголовок = м.get("текст", "")[:40]
                break
        чаты.append({
            "имя_файла": имя_файла,
            "создан": данные.get("создан", ""),
            "завершён": данные.get("завершён", False),
            "заголовок": заголовок,
            "сообщений": len(сообщения),
        })

    активные = sorted(
        [ч for ч in чаты if not ч["завершён"]],
        key=lambda ч: ч["создан"], reverse=True
    )
    завершённые = sorted(
        [ч for ч in чаты if ч["завершён"]],
        key=lambda ч: ч["создан"], reverse=True
    )
    return активные + завершённые


def прочитать_чат(имя_файла):
    """Возвращает данные чата целиком (или None)."""
    return _загрузить(имя_файла)


def сообщения_для_ии(имя_файла):
    """Возвращает список сообщений в формате, который понимает Ollama:
    [{"role": "user"/"assistant", "content": "..."}, ...]"""
    данные = _загрузить(имя_файла)
    if данные is None:
        return []
    результат = []
    for м in данные.get("сообщения", []):
        роль = "user" if м.get("роль") == "user" else "assistant"
        результат.append({"role": роль, "content": м.get("текст", "")})
    return результат