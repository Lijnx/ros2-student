# Наблюдение графа ПР01

Дата опыта: 2026-09-27. Все процессы запущены в одном Docker-контейнере с
ROS 2 Lyrical, `rmw_fastrtps_cpp`; симулятор работал непрерывно в домене 16.
Выводы CLI сохранены рядом с этим файлом.

## Исправная связь

В терминале A запущен `ros2 run turtlesim turtlesim_node`, в B —
`ros2 run turtlesim turtle_teleop_key`. Команда
`ros2 node list --no-daemon --spin-time 2` обнаружила `/turtlesim` и
`/teleop_turtle` ([вывод](nodes-before.txt)).

`/teleop_turtle` публикует `geometry_msgs/msg/Twist` в
`/turtle1/cmd_vel`; `/turtlesim` подписан на этот топик и публикует
`turtlesim_msgs/msg/Pose` в `/turtle1/pose`. Дополнительно симулятор
публикует `/turtle1/color_sensor` (`turtlesim_msgs/msg/Color`). Служебные
топики `/parameter_events` и `/rosout` тоже присутствуют. Полный список
типов — [topics.txt](topics.txt), интерфейсы нод —
[turtlesim-info.txt](turtlesim-info.txt) и [teleop-info.txt](teleop-info.txt).
У симулятора также есть сервисы `/spawn`, `/kill`, `/clear`, `/reset`,
`/turtle1/set_pen`, `/turtle1/teleport_absolute`,
`/turtle1/teleport_relative` и action `/turtle1/rotate_absolute`.

`ros2 topic type /turtle1/pose` вернул `turtlesim_msgs/msg/Pose`. Команда
`ros2 topic echo /turtle1/pose --once` получила исходную позу
`x=5.5444445610, y=5.5444445610, theta=0`. После нажатия ↑ в терминале B
получена поза `x=7.5604443550, y=5.5444445610`: черепаха переместилась.
Файлы: [pose-before.txt](pose-before.txt),
[pose-after-working.txt](pose-after-working.txt).

Замер `ros2 topic hz /turtle1/pose` шёл с 09:53:30 до 09:53:43 UTC,
то есть 13 секунд с учётом запуска CLI; сам замер остановлен после 12 секунд.
Последняя оценка — **62.497 Гц**, окно 687 сообщений. Поза поступала даже
при неподвижной черепахе. Вывод — [pose-hz.txt](pose-hz.txt); код 124
соответствует заданному `timeout`.

## Разрыв связи

Teleop остановлен через `Ctrl+C` и заново запущен с `ROS_DOMAIN_ID=17`.
Симулятор сохранил домен 16. В терминале C после `export ROS_DOMAIN_ID=17`
та же команда `ros2 node list --no-daemon --spin-time 2` увидела только
`/teleop_turtle` ([nodes-broken.txt](nodes-broken.txt)). Проверка:

```bash
timeout 5s ros2 topic echo /turtle1/pose turtlesim_msgs/msg/Pose --once
```

завершилась кодом **124**: поза за пять секунд не поступила. Тип задан
явно, поскольку в домене 17 издатель позы не обнаруживается. При нажатии ↑
поза симулятора, считанная отдельно в домене 16, осталась
`x=7.5604443550, y=5.5444445610` — та же, что перед разрывом
([pose-after-broken-key.txt](pose-after-broken-key.txt)).

Причина: участники разных ROS-доменов не обнаруживают конечные точки друг
друга. Процессы работали, но издатель команды и подписчик симулятора не
сопоставились. Изменение переменной в оболочке не перенастраивает уже
запущенную ноду.

## Восстановление

Teleop снова остановлен и запущен с `ROS_DOMAIN_ID=16`; в C возвращён
тот же домен. `ros2 node list --no-daemon --spin-time 2` вновь показал
обе ноды ([nodes-fixed.txt](nodes-fixed.txt)). Та же проверка с
`timeout 5s ros2 topic echo ... --once` получила позу и код **0**
([pose-fixed.txt](pose-fixed.txt), [pose-fixed-exit.txt](pose-fixed-exit.txt)).
После ↑ координата `x` выросла с `7.5604443550` до `9.5764446259`
([pose-after-fixed-key.txt](pose-after-fixed-key.txt)).

Повторены те же наблюдения: состав графа, получение позы и изменение
координаты. Исправление состояло только в перезапуске teleop в исходном
домене; симулятор и ROS 2 не переустанавливались.
