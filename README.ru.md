<p align="center">
  <img src="icon/ALLtoCEF.png" alt="ALL to CEF icon" width="200">
</p>

<h1 align="center">ALL to CEF</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python">
  <img alt="License" src="https://img.shields.io/badge/license-Non--commercial-lightgrey">
</p>

ALL to CEF — это набор утилит и графический интерфейс для экспериментов с логами. Он позволяет создавать регулярные выражения, подсвечивать логи и генерировать код для преобразования в формат CEF (Common Event Format).

## Возможности

- 🖥️ **Интерфейс Tkinter** для просмотра логов и переключения шаблонов.
- 🧙 **Мастер шаблонов** строит черновые регулярные выражения из выбранных строк с управлением числами, регистром и объединением префиксов.
- 📚 **Встроенные шаблоны** для распространённых временных меток и сообщений плюс пользовательские расширения.
- 🎨 **Подсветка покрытия** показывает, какие части лога совпали, и считает процент покрытых символов.
- 📊 **Анализ покрытия** перечисляет строки без ключевых полей CEF и показывает общую статистику.
- 🛠️ **Генератор кода** создаёт Python‑конвертер в CEF с трансформациями, заменами, перестановкой токенов и счётчиками.
- 🗂️ **Примерные логи** в `data/sample_logs` для быстрой проверки.

## Установка

1. Убедитесь, что установлен Python версии 3.11 или новее.
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

Если нет доступа к сети, установите пакеты из `requirements.txt` в виртуальное окружение и используйте его.

## Запуск приложения

Запустите GUI командой:

```bash
python main.py
```

Откройте файл лога через меню **Команды**, выделите строки и запустите **Создать шаблон**, чтобы построить новый шаблон. Используйте **Сохранить шаблоны** в том же меню для сохранения шаблонов или выберите **Генератор кода** для создания конвертера CEF.

## Создание инсталлятора

Для сборки самостоятельного исполняемого файла нужен [PyInstaller](https://pyinstaller.org). Установите его и выполните скрипт:

```bash
pip install pyinstaller
python build_installer.py
```

Готовый установщик `ALLtoCEF` появится в папке `dist` и будет использовать иконку из `icon/ALLtoCEF.png`. Скрипт также упакует эту иконку и необходимые файлы шаблонов, CEF и переводов.

## Запуск тестов

Репозиторий содержит обширный набор тестов. Запустите их так:

```bash
pytest -q
```

Все тесты должны проходить после установки зависимостей.

## Трансформации

При описании правил сопоставления для генератора кода поддерживаются следующие преобразования:

- `lower`, `upper`, `capitalize`, `sentence`
- `time` — распознаёт многие форматы даты и времени через `python-dateutil` и преобразует их в `YYYY-MM-DDTHH:MM:SSZ`.

Также можно задавать перестановку токенов, замену значений и карты соответствия. Подробнее см. в `utils/transform_logic.py`.

Для полей категории `Time` эти трансформации применяются по умолчанию.

## Структура проекта

```
core/   – конструктор regex, токенизатор и логика подсветки
utils/  – утилиты для JSON, цвета и генератор кода
gui/    – модули пользовательского интерфейса на Tkinter
data/   – встроенные шаблоны, определения полей CEF и примеры логов
```

## Документация

Подробные описания окон и инструментов находятся в каталоге [docs](docs/).

## UML‑диаграммы

Автоматически созданные диаграммы классов и пакетов расположены в [docs/uml](docs/uml).

## Ссылка на источник

Примеры логов для проекта взяты из репозитория [loghub](https://github.com/logpai/loghub). Использована следующая работа:

Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu. [Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics](https://arxiv.org/abs/2008.06448). IEEE International Symposium on Software Reliability Engineering (ISSRE), 2023.

## Лицензия

Проект распространяется под [некоммерческой лицензией](LICENSE).
