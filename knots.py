from dataclasses import dataclass


@dataclass(frozen=True)
class SmallKnot:
    knot_id: str
    name: str
    threads: tuple  # 3 thread names
    unlock_text: str


@dataclass(frozen=True)
class TransformationKnot:
    knot_id: str
    name: str
    type_emoji: str
    threads: tuple  # all threads of the type
    unlock_text: str


SMALL_KNOTS: list[SmallKnot] = [
    SmallKnot(
        "otpuskaniya",
        "Узел Отпускания",
        ("Обиды", "Потери", "Забвения"),
        "Нити Обиды, Потери и Забвения сошлись. Ты несёшь что-то, что давно просит покоя."
        " Пришло время посмотреть на это.",
    ),
    SmallKnot(
        "vstrechi_s_soboj",
        "Узел Встречи с Собой",
        ("Зеркала", "Стыда", "Тела"),
        "Нити Зеркала, Стыда и Тела показали путь внутрь. Ты близко к тому,"
        " кем являешься на самом деле.",
    ),
    SmallKnot(
        "vygoraniya",
        "Узел Выгорания",
        ("Усталости", "Вины", "Паузы"),
        "Нити Усталости, Вины и Паузы сошлись — они знают, что ты устал(а) не от лени,"
        " а от слишком многого. Пора остановиться.",
    ),
    SmallKnot(
        "yarosti_i_sily",
        "Узел Ярости и Силы",
        ("Гнева", "Ярости", "Границ"),
        "Нити Гнева, Ярости и Границ указывают на одно: где-то твоя сила не нашла выхода."
        " Давай направим её.",
    ),
    SmallKnot(
        "trevogi",
        "Узел Тревоги",
        ("Сомнений", "Хаоса", "Безопасности"),
        "Нити Сомнений, Хаоса и Безопасности сплелись в знакомый клубок."
        " Тревога здесь — это сигнал, не приговор.",
    ),
    SmallKnot(
        "tsennosti",
        "Узел Ценности",
        ("Денег", "Зависти", "Голода"),
        "Нити Денег, Зависти и Голода указывают в одно место — туда, где живёт"
        " твоё ощущение собственной ценности.",
    ),
    SmallKnot(
        "blizosti",
        "Узел Близости",
        ("Одиночества", "Нежности", "Любви"),
        "Нити Одиночества, Нежности и Любви нашли друг друга."
        " Ты готов(а) открыться близости.",
    ),
    SmallKnot(
        "istseleniya",
        "Узел Исцеления",
        ("Слёз", "Печали", "Благодарности"),
        "Нити Слёз, Печали и Благодарности сошлись в редкую тройку."
        " Горе и благодарность — две стороны одного чувства.",
    ),
    SmallKnot(
        "dejstviya",
        "Узел Действия",
        ("Воли", "Выбора", "Свободы"),
        "Нити Воли, Выбора и Свободы указывают в одну сторону — вперёд."
        " Что-то в тебе уже знает следующий шаг.",
    ),
    SmallKnot(
        "novogo_nachala",
        "Узел Нового Начала",
        ("Вины", "Принятия", "Новой Нити"),
        "Нити Вины, Принятия и Новой Нити завершают цикл. Ты отпускаешь, принимаешь"
        " и готовишься начать заново.",
    ),
]

TRANSFORMATION_KNOTS: list[TransformationKnot] = [
    TransformationKnot(
        "velikoj_tishiny",
        "Узел Великой Тишины",
        "🧶",
        ("Тишины", "Паузы", "Пустоты", "Зеркала", "Забвения"),
        "Ты прошёл(прошла) через все оттенки тишины. Внутри больше нет шума — только ты.",
    ),
    TransformationKnot(
        "prinyatoj_teni",
        "Узел Принятой Тени",
        "🔥",
        ("Гнева", "Стыда", "Обиды", "Зависти", "Вины"),
        "Ты встретил(а) всё, что пряталось в тени — и не убежал(а). Это требует мужества.",
    ),
    TransformationKnot(
        "glubinnyh_vod",
        "Узел Глубинных Вод",
        "🌊",
        ("Печали", "Одиночества", "Слёз", "Потери", "Нежности"),
        "Все воды пройдены. Ты умеешь чувствовать — по-настоящему, без страха утонуть.",
    ),
    TransformationKnot(
        "tvjordoj_pochvy",
        "Узел Твёрдой Почвы",
        "🌍",
        ("Тела", "Денег", "Усталости", "Безопасности", "Дома", "Голода"),
        "Земля под ногами стала твоей. Ты знаешь, где твоё тело, ресурсы и дом.",
    ),
    TransformationKnot(
        "svobodnogo_uma",
        "Узел Свободного Ума",
        "💨",
        ("Выбора", "Сомнений", "Свободы", "Мыслей", "Хаоса", "Дыхания"),
        "Ум перестал быть тюрьмой. Ты видишь мысли — но не растворяешься в них.",
    ),
    TransformationKnot(
        "zhivogo_ognya",
        "Узел Живого Огня",
        "⚡",
        ("Границ", "Импульса", "Воли", "Страсти", "Ярости"),
        "Огонь больше не жжёт изнутри. Он светит.",
    ),
    TransformationKnot(
        "chistogo_sveta",
        "Узел Чистого Света",
        "✨",
        ("Радости", "Благодарности", "Надежды", "Любви", "Новой Нити", "Принятия", "Смысла"),
        "Свет собран полностью. Ты прошёл(прошла) путь от первой нити до последней."
        " Это уже трансформация.",
    ),
]

# Fast lookup: thread_name → knots that include it
_THREAD_TO_SMALL: dict[str, list[SmallKnot]] = {}
for _k in SMALL_KNOTS:
    for _t in _k.threads:
        _THREAD_TO_SMALL.setdefault(_t, []).append(_k)

_THREAD_TO_TRANSFORMATION: dict[str, TransformationKnot] = {}
for _k in TRANSFORMATION_KNOTS:
    for _t in _k.threads:
        _THREAD_TO_TRANSFORMATION[_t] = _k


def get_new_knots(
    thread_name: str,
    user_threads: set,        # thread names received at least once
    user_unlocked: set,       # already unlocked knot_ids
) -> list:
    """Return list of newly unlocked SmallKnot / TransformationKnot objects."""
    new_knots = []

    for knot in _THREAD_TO_SMALL.get(thread_name, []):
        if knot.knot_id not in user_unlocked:
            if all(t in user_threads for t in knot.threads):
                new_knots.append(knot)

    tk = _THREAD_TO_TRANSFORMATION.get(thread_name)
    if tk and tk.knot_id not in user_unlocked:
        if all(t in user_threads for t in tk.threads):
            new_knots.append(tk)

    return new_knots
