# Использование ИИ

## PR01

- Использован ИИ: да, Codex (GPT-6), интерфейс Codex desktop.
- Затронутые файлы: README.md, .github/workflows/pr01.yml,
  evidence/pr01/graph.md, evidence/pr01/environment.json,
  evidence/pr01/report.json и эта декларация.
- Помощь: консультации по графу ROS 2, топикам и доменам; уточнение команд
  опыта, требований отчёта и CI; оформление перечисленных файлов.
- Проверка: вывод команд и результаты опыта получены при запуске ROS 2 в
  контейнере; изменения позы, состав графа и коды завершения сопоставлены
  с сохранёнными наблюдениями. Состав evidence проверен course kit и CI.
- Теоретические пояснения и краткий сценарий демонстрации подготовлены
  отдельно от репозитория.

## PR02

- Использован ИИ: да, Codex (GPT-6), интерфейс Codex desktop.
- Затронутые файлы: README.md, .github/workflows/pr01.yml,
  .github/workflows/pr02.yml, src/turtle_bringup/package.xml,
  src/turtle_bringup/setup.py, src/turtle_bringup/launch/sim.launch.py,
  evidence/pr02/commands.md, evidence/pr02/types.md,
  evidence/pr02/report.json и эта декларация.
- Помощь: консультации по структуре пакета ROS 2, launch и полным именам
  топиков; уточнение команд проверки, CI и оформление перечисленных файлов.
- Проверка: пакет собран в ROS-контейнере, launch запущен и остановлен;
  доставка команды проверена по графу и изменению позы до сбоя и после
  исправления. Комплектность evidence проверена course kit и GitHub CI.
- Теоретические пояснения и краткий сценарий демонстрации подготовлены
  отдельно от репозитория.

## PR03

- Использован ИИ: да, Codex (GPT-6), интерфейс Codex desktop.
- Затронутые файлы: README.md, .github/workflows/pr03.yml,
  src/patrol/package.xml, src/patrol/setup.py, src/patrol/patrol/control.py,
  src/patrol/patrol/patrol.py, src/patrol/test/test_control.py,
  evidence/pr03/demo.md, evidence/pr03/report.json и эта декларация.
- Помощь: консультации по устройству ноды, подписки, таймера и remap;
  подготовка кода пакета, тестов, команд демонстрации и CI.
- Проверка: пакет собран в ROS-контейнере, тесты запущены через pytest и
  colcon; разрыв связи и исправление проверены по конечным точкам графа,
  позе и частоте команд. Состав evidence проверен course kit и GitHub CI.
- Теоретические пояснения и краткий сценарий демонстрации подготовлены
  отдельно от репозитория.

Переписка, личные промпты и секреты не включены.
