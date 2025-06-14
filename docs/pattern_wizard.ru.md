# 🧙 Мастер шаблонов

В этом документе описан диалог **Pattern Wizard** из `gui/pattern_wizard.py`. Мастер помогает создавать регулярные выражения по примерам строк из лога.

## Назначение

Мастер шаблонов предоставляет интерактивный процесс построения черновых регулярных выражений на основе выбранных фрагментов. Пользователь может настраивать параметры генерации, просматривать совпадения по всему логу и сохранять новые шаблоны для использования в основном приложении.

## Запуск

В главном окне выделите текст в просмотрщике логов и нажмите **Создать шаблон**. Программа соберёт выбранные фрагменты, попросит имя для шаблонов этого лога и затем откроет мастер.

## Обзор интерфейса

1. **Меню** – содержит единственный пункт **Сохранить** с сочетанием `Ctrl+S`.
2. **Имя** и **Категория** – поля в верхней части. Категория выбирается автоматически на основе отмеченных CEF‑полей (см. ниже).
3. **Показать дополнительные настройки** – показывает или скрывает дополнительные параметры.
4. **Дополнительные параметры**:
   - **Игнорировать регистр** – компилировать regex с флагом `re.IGNORECASE`.
   - **Режим чисел** – управляет генерализацией числовых токенов. Варианты: Standard, Fixed length, Always `\d+`, Set minimum length и Fixed or minimum length.
   - **Мин. длина числа** – используется некоторыми режимами чисел.
   - **Объединение текста** – рассматривать разные слова как один столбец токенов.
   - **Использовать |** – при возможности предпочитать перечисления (`foo|bar`).
   - **Объединение по префиксу** – объединять альтернативы с общими префиксом и суффиксом.
   - **Макс. вариантов** – максимальная длина перечислений, создаваемых конструктором regex.
   - **Окно слева/справа** – дополнительные якоря слева и справа для окна фрагмента.
5. **Сгенерированное регулярное выражение** – редактируемая область с черновым regex. Ниже находится комбобокс фрагментов для вставки готовых частей.
6. **← Назад** – восстанавливает предыдущий regex из истории (`Ctrl+Z`).
7. **Обновить** – заново генерирует regex из текущих примеров и параметров (`Ctrl+R`).
8. **Применить** – компилирует regex и показывает совпадения в области предпросмотра (`Ctrl+Enter`).
9. **Примеры** – список выбранных фрагментов. Кнопки позволяют удалять записи (`Удалить`) или добавлять новую выборку из предпросмотра (`Ctrl+A`).
10. **Предпросмотр совпадений** – показывает строки лога с подсветкой совпадений. Отображает подходящие строки, отсутствующие строки или строки с несколькими совпадениями (конфликты). Используйте `Alt+Left`/`Alt+Right` для перехода по страницам.
11. **Поля CEF** – список галочек полей CEF с поиском. Выбранный набор определяет категорию, которая обновляется автоматически. Подсказки показывают описания и примеры полей.

## Сниппеты

Выпадающий список сниппетов позволяет быстро вставлять распространённые фрагменты regex, такие как:

- Одно слово (`\S+`)
- Слово только из букв (`[a-zA-Z]+`)
- Только цифры (`\d+`)
- Буквенно‑цифровое слово (`[a-zA-Z0-9]+`)
- Слово из любых символов (`[^ \t\n\r\f\v]+`)
- До конца строки (`.*`)
- До конца строки (ленивое) (`.*?`)
- Число фиксированной длины (3) (`\d{3}`)
- Число минимум из N цифр (`\d{2,}`)
- Символы до двоеточия (`[^:]+`)
- Фрагмент в `[]` (`\[[^\]]+\]`)
- Фрагмент в `()` (`\([^)]+\)`)
- Строка с тегом (`[a-zA-Z0-9._-]+:`)

Выбор сниппета вставляет соответствующий текст в редактор regex.

## Генерация regex

Мастер использует `core.regex.regex_builder.build_draft_regex_from_examples` для создания выражения на основе примеров. Функция принимает описанные выше параметры и анализирует столбцы токенов во всех строках. Она распознаёт пары ключ‑значение и может объединять токены или строить перечисления. Сгенерированное выражение сохраняется в истории, поэтому кнопка **← Назад** может отменить изменения.

После применения выражения совпадения подсвечиваются в виджете предпросмотра с помощью `core.regex_highlighter.apply_highlighting` и жёлтого цвета.

## Сохранение шаблонов

Действие **Save** собирает имя, категорию, текст regex и выбранные поля CEF. Данные записываются в `user_patterns.json` и в шаблоны для текущего лога через функции `utils.json_utils` (`save_user_pattern` и `save_per_log_pattern`). После сохранения диалог закрывается.

## Автовыбор категории

Когда поля CEF отмечаются или снимаются, мастер автоматически выбирает категорию. Если все выбранные поля принадлежат одной категории, устанавливается она. Если поля из разных категорий, используется специальное значение «Multiple».

## Тесты

`tests/test_pattern_wizard.py` проверяет основные вспомогательные методы:

- `_on_digit_mode_change` – соответствие внутреннего значения выбранному режиму.
- `_push_history` и `_undo_regex` – работа с историей regex.
- `_toggle_advanced` – показ и скрытие блока дополнительных параметров.
- `_filter_cef_fields` – фильтрация списка полей по строке поиска.
- `_auto_select_category` – обновление категории по отмеченным полям.
- `_on_snippet_selected` – вставка текста сниппета в поле regex.

## UML‑диаграммы

Диаграммы классов и пакетов, созданные PlantUML, находятся в `docs/uml`. Файл `classes_LogParserHelper.plantuml` содержит атрибуты `PatternWizardDialog` и других классов GUI.

## Итог

Мастер шаблонов — это мощный инструмент для создания новых правил разбора логов. Он проводит пользователя от выбора примеров через настройку параметров и просмотр результатов до сохранения шаблона для дальнейшего применения.
