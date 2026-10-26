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

## PR04

- Использован ИИ: да, Codex (GPT-6), интерфейс Codex desktop.
- Затронутые файлы: README.md, .github/workflows/pr03.yml,
  .github/workflows/pr04.yml, src/patrol/package.xml,
  src/patrol/patrol/control.py, src/patrol/patrol/patrol.py,
  src/patrol/test/test_control.py, src/patrol/test/test_parameters.py,
  evidence/pr04/parameters.md, evidence/pr04/report.json и эта декларация.
- Помощь: консультации по параметрам ROS 2, проверке входов и замене таймера;
  подготовка правок кода, тестов, команд демонстрации и CI.
- Проверка: пакет собран и протестирован в ROS-контейнере; допустимые и
  ошибочные параметры проверены по ответам сервиса, состоянию ноды и
  частоте потока. Намеренный дефект воспроизведён отдельно, после
  исправления те же действия повторены. Комплектность проверена course kit
  и GitHub CI.
- Теоретические пояснения и краткий сценарий демонстрации подготовлены
  отдельно от репозитория.

## PR05

- Использован ИИ: да, GPT-6.1 Sol, интерфейс OpenCode.
- Затронутые файлы: README.md, .gitignore, .github/workflows/pr04.yml,
  .github/workflows/pr05.yml, src/patrol/patrol/patrol.py,
  src/course_bringup/package.xml, src/course_bringup/setup.py,
  src/course_bringup/setup.cfg, src/course_bringup/resource/course_bringup,
  src/course_bringup/course_bringup/{__init__,qos,pose_relay,pose_subscriber}.py,
  src/course_bringup/launch/patrol.launch.py,
  src/course_bringup/config/qos-overrides.yaml, config/qos-overrides.yaml,
  src/course_bringup/test/{test_qos,test_style}.py,
  evidence/pr05/ и эта декларация.
- Помощь: консультации по launch, namespace, remap, совместимости QoS и MCAP;
  подготовка пакета, тестов, сценария опыта, CI и оформления результатов.
- Проверка: все пакеты собраны и протестированы в ROS-контейнере; несовместимые
  профили и исправление проверены по конечным точкам графа, счётчику приложения
  и CLI на живом потоке и повторе одной записи. Проверены отсутствие recorder
  при record=false, движение, другой namespace и завершение процессов;
  неизменность MCAP подтверждена SHA-256. Комплектность проверена course kit;
  GitHub CI выполняет сборку, функциональные тесты пакетов и checker;
  живой опыт с turtlesim, записью и replay проверен локально.
- Теоретические пояснения и подробный сценарий демонстрации подготовлены
  отдельно от репозитория.
- Дополнительная автоматизация эксперимента удалена по просьбе пользователя;
  для повторения оставлены команды ROS 2 в README, результаты опыта сохранены.

Переписка, личные промпты и секреты не включены.
