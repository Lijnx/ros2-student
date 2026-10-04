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
