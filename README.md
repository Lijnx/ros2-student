# ПР01. Окружение и граф ROS 2

Опыт выполнен с `turtlesim` в ROS 2 Lyrical. Проверены работающий граф,
поток `/turtle1/pose`, разрыв связи разными `ROS_DOMAIN_ID` и её восстановление.
Результаты и фактические значения записаны в [graph.md](evidence/pr01/graph.md).

## Среда

Использован WSL2 с Docker и отображением окна через WSLg. Образ закреплён
по digest:

```text
osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe
```

Из корня репозитория запустить один контейнер. Для показа окна требуется
доступный X11 `DISPLAY` и сокет `/tmp/.X11-unix`:

```bash
docker run -d --name pr01-ros2 --network bridge \
  -e DISPLAY -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD:/work" -w /work \
  osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe \
  sleep infinity
```

Открыть три терминала в **том же контейнере**. В каждом выполнить:

```bash
docker exec -it pr01-ros2 bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
cd /work
```

В терминале A работает симулятор, в B — управление. Стрелки нажимаются
при фокусе в терминале B:

```bash
# A
ros2 run turtlesim turtlesim_node

# B
ros2 run turtlesim turtle_teleop_key
```

В C наблюдать граф и сохранить фактический вывод:

```bash
mkdir -p evidence/pr01
ros2 doctor --report > evidence/pr01/doctor.txt 2>&1
ros2 node list --no-daemon --spin-time 2
ros2 topic list -t
ros2 node info /turtlesim
ros2 node info /teleop_turtle
POSE_TYPE=$(ros2 topic type /turtle1/pose)
ros2 topic echo /turtle1/pose --once
ros2 topic hz /turtle1/pose # не менее 10 секунд, затем Ctrl+C
```

Проверить изменение позы после нажатия ↑ в B. Для воспроизведения дефекта
остановить B через `Ctrl+C`, установить там `ROS_DOMAIN_ID=17` и вновь
запустить `turtle_teleop_key`. A остаётся в домене 16. В C:

```bash
export ROS_DOMAIN_ID=17
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once
echo "exit=$?"
```

Ожидаются только `/teleop_turtle` и код 124: подписчик за пять секунд
не получил позу. Тип указан явно, поскольку в домене 17 нет издателя,
у которого CLI мог бы его узнать. Нажатие ↑ в B не перемещает черепаху.

Для исправления остановить B, вернуть `ROS_DOMAIN_ID=16`, вновь запустить
teleop и повторить в C **ту же** проверку:

```bash
export ROS_DOMAIN_ID=16
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once
echo "exit=$?"
```

Теперь видны обе ноды, получена поза, код равен 0, управление снова работает.
Новое значение переменной окружения влияет на запускаемые после него
процессы, поэтому teleop перезапускается. Симулятор не перезапускался.

## Проверка состава сдачи

Выпуск course kit `v1-w03` и его SHA-256 закреплены в
`evidence/pr01/report.json` и GitHub Actions workflow. Из корня репозитория:

```bash
curl -fsSLo course-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w03-7fbfd3e8161a.tar.gz
printf '%s  %s\n' \
  7fbfd3e8161ab6c6ebefc7663efdaf77d9a7d490399743507f33dcefbd5ac522 \
  course-kit.tar.gz | sha256sum -c -
mkdir -p .course-kit
tar -xzf course-kit.tar.gz -C .course-kit
python3 -m json.tool evidence/pr01/environment.json >/dev/null
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```

Этот checker проверяет состав файлов и отчёт. Доставку сообщений и движение
черепахи подтверждают записи в `evidence/pr01/` и повторение опыта.

# ПР02. Пакет и запуск turtlesim

ПР02 добавляет пакет `turtle_bringup` и установленный launch-файл. Результаты
сборки, команды и сравнение правильного и ошибочного топика находятся в
`evidence/pr02/`. Используется тот же ROS 2 Lyrical-образ и графическое
окружение, что описаны выше.

В одном контейнере из корня репозитория подключить ROS и собрать пакет:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
colcon build --symlink-install --packages-select turtle_bringup
source install/setup.bash
ros2 pkg prefix turtle_bringup
ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
```

В терминале A запустить симулятор и оставить команду работать:

```bash
ros2 launch turtle_bringup sim.launch.py
```

В другом терминале того же контейнера подключить ROS и тот же домен.
Проверить ноду и позу, затем отправить команду:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
ros2 node list --no-daemon --spin-time 2
ros2 topic echo /turtle1/pose --once
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
ros2 topic echo /turtle1/pose --once
```

Для сбоя запустить публикацию с **тем же** типом и значением в `/cmd_vel`:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

В третьем терминале `ros2 topic info /cmd_vel --verbose` покажет издателя
без подписчика. У `/turtle1/cmd_vel` будет подписчик без издателя; поза не
изменится. Остановить издатель через `Ctrl+C` и повторить **ту же** команду,
заменив только `/cmd_vel` на `/turtle1/cmd_vel`. Теперь видны обе конечные
точки и черепаха движется. После опыта остановить издатель и launch.

GitHub Actions собирает пакет, проверяет установленный launch-файл и
запускает checker course kit `v1-w03`. Живой GUI-опыт проверен локально;
числа и вывод CLI приведены в `evidence/pr02/commands.md`.

# ПР03. Первая нода: поза и команда

Пакет `patrol` на ROS 2 Lyrical подписывается на `/turtle1/pose` и каждые
0,1 с публикует `geometry_msgs/msg/Twist`. Пока pose не получена, все поля
команды нулевые; после первого сообщения `linear.x=0.5` и `angular.z=0.3`.
Топик издателя задан относительным именем `cmd_vel`, чтобы можно было показать
разрыв связи и исправить его remap при запуске. Код и тесты находятся в
`src/patrol/`, наблюдения в `evidence/pr03/`.

В терминале A того же ROS-контейнера:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
ros2 launch turtle_bringup sim.launch.py
```

В терминале B подключить те же setup и `ROS_DOMAIN_ID=16`, затем сначала
запустить вариант с ошибочным адресом:

```bash
ros2 run patrol patrol
```

В терминале C после подключения ROS проверить граф: у `/cmd_vel` есть
издатель без подписчика, а у `/turtle1/cmd_vel` подписчик без издателя.
Остановить patrol в B через `Ctrl+C` и перезапустить с remap:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

Теперь `ros2 topic info /turtle1/cmd_vel --verbose` показывает обе конечные
точки, а `ros2 topic hz /turtle1/cmd_vel` измеряет около 10 Гц. Точные команды
и результаты до и после исправления приведены в `evidence/pr03/demo.md`.
Остановить patrol через `Ctrl+C`, затем дождаться нулевой скорости turtlesim
и остановить launch.

Функциональные тесты и линтеры запускать из каталога пакета, чтобы созданные
`ament`-тесты не сканировали соседний пакет и артефакты `build/`:

```bash
(cd src/patrol && python3 -m pytest test -q)
colcon test --packages-select patrol --event-handlers console_direct+
colcon test-result --verbose
python3 .course-kit/v1/tools/check_practice.py PR03 --submission .
```

CI повторяет сборку, тесты и checker с закреплённым course kit `v1-w04`.

# ПР04. Параметры движения

Нода `patrol` теперь объявляет `linear_speed=0.5`, `turn_rate=0.3` и
`publish_hz=10.0`. Во время работы допустимы конечные значения в диапазонах
`0–1 м/с`, `−1–1 рад/с` и `1–30 Гц`. Обновление проверяется до изменения
состояния; при смене частоты старый таймер уничтожается и создаётся один
новый. Нулевую и отрицательную частоту, а также `NaN` нода отклоняет.

После сборки пакета запустить симулятор из ПР02 с `ROS_DOMAIN_ID=17`.
В другом терминале:

```bash
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=17
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

В третьем терминале с той же средой:

```bash
ros2 param set /patrol publish_hz 5.0
ros2 param set /patrol publish_hz 0.0
ros2 param get /patrol publish_hz
ros2 topic hz /turtle1/cmd_vel
```

Полные команды и фактические результаты до и после намеренного дефекта
записаны в `evidence/pr04/parameters.md`. Тесты пакета и checker запускаются
по порядку из раздела ПР03, заменив в последней команде `PR03` на `PR04`.

# ПР05. Launch, QoS и повтор записи

`course_bringup` запускает один глобальный turtlesim, прежний `patrol`,
`pose_relay` и отдельный `pose_subscriber`. Ноды курса находятся в `/robot_a`;
поза и команда turtlesim подключены через remap. Все имена топиков в коде
нод относительные. При запуске `patrol` без namespace его поведение из ПР04
сохраняется.

Relay копирует позу в `/robot_a/sensor_pose`: `best_effort`, `volatile`,
`keep_last`, depth=10. Подписчик выбирает `reliable` или `best_effort` при
старте и раз в секунду пишет число полученных сообщений. Параметр reliability
read-only: для смены QoS нужно пересоздать подписку, здесь — перезапустить ноду.

## Сборка и запуск

Используется тот же закреплённый ROS 2 Lyrical-образ из ПР01. Все команды
выполняются из корня workspace внутри одного контейнера. Можно использовать
уже работающий ROS-контейнер либо создать отдельный:

```bash
docker run -d --name pr05-ros2 -e DISPLAY -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix -v "$PWD:/work" -w /work \
  osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe \
  sleep infinity
docker exec -it pr05-ros2 bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=25
colcon build --symlink-install
source install/setup.bash
ros2 launch course_bringup patrol.launch.py --show-args
```

В каждом следующем терминале подключить ROS, `install/setup.bash` и тот же
домен. Для работы без окна вместо настройки X11 задать
`export QT_QPA_PLATFORM=offscreen`; сам turtlesim и обмен сообщениями работают.

```bash
# A: намеренная несовместимость; запись не запускается.
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=reliable record:=false

# B: топик виден, но echo завершается с exit=124.
ros2 topic info /robot_a/sensor_pose --verbose --no-daemon --spin-time 2
timeout 4s ros2 topic echo /robot_a/sensor_pose turtlesim_msgs/msg/Pose \
  --qos-reliability reliable --once
echo "exit=$?"
```

Остановить A через `Ctrl+C`. Затем запустить исправленный вариант:

```bash
# A: каталог bag_dir должен быть новым; recorder включён через IfCondition.
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=best_effort \
  record:=true bag_dir:=log/pr05-manual-bag

# B: теперь echo получает позу, exit=0.
timeout 4s ros2 topic echo /robot_a/sensor_pose turtlesim_msgs/msg/Pose \
  --qos-reliability best_effort --once
echo "exit=$?"
```

Дать записи поработать 10–15 секунд и остановить **весь launch** через `Ctrl+C`:
recorder завершит MCAP и metadata. Replay запускать только после остановки
живых нод:

```bash
# A: одна и та же запись для обоих подписчиков.
ros2 bag play log/pr05-manual-bag --loop \
  --qos-profile-overrides-path config/qos-overrides.yaml

# B: первый запрос — exit=124, второй — exit=0.
timeout 4s ros2 topic echo /robot_a/sensor_pose turtlesim_msgs/msg/Pose \
  --qos-reliability reliable --once
echo "exit=$?"
timeout 4s ros2 topic echo /robot_a/sensor_pose turtlesim_msgs/msg/Pose \
  --qos-reliability best_effort --once
echo "exit=$?"
ros2 bag info log/pr05-manual-bag
```

Остановить player через `Ctrl+C`. `config/qos-overrides.yaml` относится к
контрактному `/robot_a/sensor_pose`; для replay другого namespace нужно
изменить ключ YAML. Launch поддерживает также `namespace:=/robot_b`:
recorder выбирает его поток динамически и адаптирует QoS к издателю.

## Проверки

В свободном домене, без других нод:

```bash
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

Функциональные тесты проверяют неизменность сериализованной позы, матрицу QoS
и отказ неизвестного профиля. CI выполняет сборку, тесты пакетов и checker.
Живой опыт с turtlesim, записью MCAP и replay выполняется только локально —
по командам выше. Для новой записи используйте новый `bag_dir`, не заменяя
сохранённый локально bag сдачи в `evidence/pr05/bag/`.

Для checker ПР05 закреплён course kit `v1-w08`:

```bash
curl -fsSLo course-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w08-aea8efd0a516.tar.gz
printf '%s  %s\n' \
  aea8efd0a51668af63f2e475b82bfa28bd76c21f20d8afea6b136d43a56a88fb \
  course-kit.tar.gz | sha256sum -c -
mkdir -p .course-kit
tar -xzf course-kit.tar.gz -C .course-kit
python3 .course-kit/v1/tools/check_practice.py PR05 --submission .
```

Фактические результаты находятся в `evidence/pr05/`: `qos-before.txt`,
`qos-after.txt`, логи процессов, `bag-metadata.yaml`, `tests.txt` и отчёт.
MCAP хранится локально в `evidence/pr05/bag/` и исключён из Git; его digest
сохранён в `qos-after.txt`. Checker проверяет комплектность evidence,
а не заменяет проверку доставки сообщений.
