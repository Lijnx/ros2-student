# ПР04: параметры работающей ноды и отказ при нулевой частоте

Окружение: ROS 2 Lyrical в образе `osrf/ros:lyrical-desktop-full`, пакет
`patrol` из ПР03, `turtle_bringup` из ПР02, `ROS_DOMAIN_ID=17`. Во всех
терминалах перед опытом выполнены:

```bash
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=17
```

## Исправный запуск и изменение параметров

Пакет собран командой `colcon build --symlink-install --packages-select
patrol turtle_bringup`. В терминале A запущен `ros2 launch turtle_bringup
sim.launch.py`, в B:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

В терминале C выполнены:

```bash
ros2 param list /patrol
ros2 param get /patrol linear_speed
ros2 param get /patrol turn_rate
ros2 param get /patrol publish_hz
ros2 topic hz /turtle1/cmd_vel
ros2 param set /patrol linear_speed 0.8
ros2 param set /patrol turn_rate -0.2
ros2 topic echo /turtle1/cmd_vel --once
ros2 param set /patrol publish_hz 5.0
ros2 param get /patrol publish_hz
ros2 topic hz /turtle1/cmd_vel
```

Изначально параметры равнялись `0.5`, `0.3`, `10.0`
(`params-initial.txt`). Измеренный поток был 10,000 Гц на окне 109
интервалов (`hz-10.txt`). После изменения скоростей опубликован Twist
с `linear.x=0.8`, `angular.z=-0.2` (`command-adjusted.txt`). После смены
частоты `ros2 param get` показал `5.0`, а `ros2 topic hz` измерил
5,000 Гц на окне 49 интервалов (`hz-after-set.txt`, `hz-5.txt`). Это
подтверждает, что прежний таймер 10 Гц больше не публикует; в коде он
отменяется и уничтожается до создания нового.

Каждое измерение `ros2 topic hz` выполнялось с ограничением 12 с командой
`timeout --signal=INT 12s ...`; код 124 в соседнем `*-exit.txt` означает
истечение окна измерения, а не ошибку ROS.

## Входы вне диапазона

При работающей ноде с частотой 5 Гц выполнены:

```bash
ros2 param set /patrol publish_hz 0.0
ros2 param get /patrol publish_hz
ros2 param set /patrol publish_hz -1.0
ros2 param get /patrol publish_hz
ros2 param set /patrol publish_hz .nan
ros2 param get /patrol publish_hz
ros2 topic hz /turtle1/cmd_vel
```

Команды изменения параметра вывели соответственно `publish_hz must be
between 1.0 and 30.0` для 0 и −1 и `publish_hz must be a finite number`
для NaN (`reject-zero.txt`, `reject-negative.txt`, `reject-nan.txt`). После
каждого отказа значение оставалось `5.0`; поток остался 5,000 Гц
(`hz-after-rejections.txt`). Значения и коды CLI сохранены в одноимённых
файлах. Отказ `ros2 param set` здесь выражается сообщением, хотя код самой
команды равен 0, поэтому при проверке нужно читать ответ и состояние ноды.

## Намеренный дефект и то же исправление

В отдельном коммите `422210be4fdcb768c8814acf7ca32607bc42ee66`
временно отключена проверка `publish_hz`. При запуске этой версии и
выполнении `ros2 param set /patrol publish_hz 0.0` в callback после принятия
значения произошло деление `1.0 / 0.0`: `ZeroDivisionError` в
`apply_parameters` (`defect-node.log`, повтор в `defect-node-repeat.log`).
Процесс завершился с кодом 1, `/patrol` исчезла из графа
(`defect-nodes-after.txt`). Клиент `ros2 param set` не получил ответ от
упавшего сервера и был остановлен через 8 с кодом 124
(`defect-set-zero-exit.txt`).

Проверка возвращена коммитом
`dd471970a42912cd9a2eada3cdc5c52a70bea1f5`. С нуля запущена нода,
установлено 5 Гц, затем повторён **тот же запрос** `publish_hz 0.0`.
Теперь сервер ответил отказом, `/patrol` и `/turtlesim` остались в графе,
параметр до и после равен `5.0`, измеренный поток остался 5,000 Гц
(`restored-reject-zero.txt`, `restored-nodes-after.txt`,
`restored-hz-after-zero.txt`).

## Сервис и действие из лекции

Команда `ros2 service call /clear std_srvs/srv/Empty '{}'` получила ответ
`std_srvs.srv.Empty_Response()` (`clear-call.txt`); это короткий запрос с
одним ответом. Команда `ros2 action list -t` нашла
`/turtle1/rotate_absolute [turtlesim_msgs/action/RotateAbsolute]`
(`actions.txt`); action принимает длительную цель поворота и может сообщать
о ходе выполнения, а не только возвращать единичный ответ.

## Тесты и быстрое повторение

Чистая функция проверена для изменения `10 → 5 Гц`, нуля, отрицательной
частоты и NaN. ROS-интеграционный тест устанавливает 5 Гц, проверяет
единственный активный таймер, затем атомарно предлагает новую скорость
вместе с нулевой частотой: оба активных значения и таймер сохраняются.
Результат `python3 -m pytest test -q` из каталога `src/patrol`:
10 passed, 1 skipped (`tests.txt`). `colcon test-result --verbose`:
11 tests, 0 errors, 0 failures, 1 skipped (`colcon-result.txt`).

Для показа преподавателю достаточно запустить исправную ноду и выполнить:

```bash
ros2 param get /patrol publish_hz
ros2 topic hz /turtle1/cmd_vel        # около 10 Гц, Ctrl+C
ros2 param set /patrol publish_hz 5.0
ros2 topic hz /turtle1/cmd_vel        # около 5 Гц, Ctrl+C
ros2 param set /patrol publish_hz 0.0
ros2 param get /patrol publish_hz     # осталось 5.0
ros2 node list                        # /patrol на месте
ros2 service call /clear std_srvs/srv/Empty '{}'
ros2 action list -t
```
