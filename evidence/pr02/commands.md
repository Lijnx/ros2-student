# Команды и наблюдения ПР02

Опыт проведён 27.09.2026 в одном Docker-контейнере с ROS 2 Lyrical,
`ROS_DOMAIN_ID=16`. Старые turtlesim и teleop были остановлены.

## Терминал и workspace

Три использованные команды Linux:

| Команда | Назначение | Полученный результат |
| --- | --- | --- |
| `pwd` | Показать текущий каталог | `/work`, корень репозитория и workspace |
| `ls -a` | Показать обычные и скрытые имена | Видны `.git`, `.github`, `src`, `evidence`, `build`, `install`, `log` |
| `mkdir -p src evidence/pr02` | Создать каталоги, в том числе вложенные | Оба каталога доступны; повторный запуск не даёт ошибки |

Вывод этих команд и сведения о среде сохранены в [workspace-check.txt](workspace-check.txt).
`ros2 pkg prefix turtlesim` вернул `/opt/ros/lyrical`, а после сборки
`ros2 pkg prefix turtle_bringup` вернул `/work/install/turtle_bringup`
([package-prefix.txt](package-prefix.txt)). Базовый и наш пакеты находятся
в разных установочных слоях.

`>` заменяет содержимое файла стандартным выводом команды; `2>&1` направляет
ошибки туда же. `|` передаёт stdout следующей программе. В
`colcon build 2>&1 | tee evidence/pr02/build.txt` программа `tee`
одновременно показывает и сохраняет вывод. `set -o pipefail` сохраняет
ненулевой статус `colcon` в конвейере. `source setup.bash` изменяет
**текущую оболочку**, в том числе пути поиска пакетов. Запуск
`bash setup.bash` создал бы новый процесс и не изменил бы окружение
терминала после его завершения. `export ROS_DOMAIN_ID=16` передаёт
настройку будущим дочерним процессам.

## Пакет и launch

Пустой `ament_python`-пакет создан командой:

```bash
cd src
ros2 pkg create --build-type ament_python --license Apache-2.0 \
  turtle_bringup --dependencies launch launch_ros turtlesim
cd ..
```

`colcon build --symlink-install --packages-select turtle_bringup` прошёл
до добавления launch-файла ([build-empty.txt](build-empty.txt)). После
добавления `launch/sim.launch.py` и записи в `data_files` файла `setup.py`
повторная сборка также прошла ([build.txt](build.txt)). Установленный файл
найден в `/work/install/turtle_bringup/share/turtle_bringup/launch/sim.launch.py`.
`python3 -m py_compile src/turtle_bringup/launch/sim.launch.py` завершился
с кодом 0.

После `source install/setup.bash` команда
`ros2 launch turtle_bringup sim.launch.py` запустила `/turtlesim`:
[nodes-running.txt](nodes-running.txt). `Ctrl+C` завершил launch и ноду:
[nodes-stopped.txt](nodes-stopped.txt) пуст. Для опыта launch запущен
вновь, его вывод сохранён в [launch-experiment.txt](launch-experiment.txt).

## Команда доходит до симулятора

Teleop не был запущен. `ros2 topic type /turtle1/pose` вернул
`turtlesim_msgs/msg/Pose`. Исходная поза:
`x=5.5444445610, y=5.5444445610, theta=0`.

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Ожидалось движение вперёд с поворотом. После одной публикации получено
`x=6.5093088150, y=5.7969908714, theta=0.5040000081`: координаты и
угол изменились. См. [pose-before.txt](pose-before.txt),
[publish-once.txt](publish-once.txt), [pose-working.txt](pose-working.txt).
Позднее скорость снова стала нулевой: единичная команда не задаёт
постоянное движение.

## Неверное имя и исправление

После остановки черепахи исходная поза для сравнения была
`x=6.5093088150, y=5.7969908714, theta=0.5040000081`
([pose-resting.txt](pose-resting.txt)). Запущен издатель:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

`ros2 topic info /cmd_vel --verbose` показал **1 издателя и 0
подписчиков** ([topic-broken.txt](topic-broken.txt)). На ожидаемом
`/turtle1/cmd_vel` были **0 издателей и 1 подписчик** turtlesim
([topic-target-during-broken.txt](topic-target-during-broken.txt)).
Оба топика имели тип `geometry_msgs/msg/Twist`, но полные имена различались.
Повторный `ros2 topic echo /turtle1/pose --once` оставил все значения
прежними: [pose-broken.txt](pose-broken.txt).

Издатель остановлен через SIGINT (эквивалент `Ctrl+C`). В команде
публикации изменено **только имя** на `/turtle1/cmd_vel`. Теперь
`ros2 topic info /turtle1/cmd_vel --verbose` показал **1 издателя и
1 подписчика** ([topic-fixed.txt](topic-fixed.txt)); новая поза стала
`x=7.4961032867, y=7.9441328049, theta=1.7680000067`
([pose-fixed.txt](pose-fixed.txt)). После остановки издателя и launch
фоновых ROS-процессов не осталось.

Причина дефекта — несовпадение **полного имени топика**, а не ошибка типа,
сборки, домена или сети. Наличие издателя в графе само по себе не
доказывает доставку конкретному подписчику.
