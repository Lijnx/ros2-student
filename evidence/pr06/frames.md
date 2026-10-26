# ПР06: системы координат и владельцы преобразований

Источник размеров: course-kit `v1-w08`, `models/course_ackermann/model.sdf`.
Колёсная база 0.8 м, колея 0.62 м, радиус колеса 0.12 м;
корпус 1.05 × 0.52 × 0.22 м, центр геометрии корпуса `(0, 0, 0.12)`.
Корень URDF — `base_link`, оси REP-103: X вперёд, Y влево, Z вверх.
Положение модели SDF в мире `(0, 0, 0.18)` не является внутренним joint
и в URDF не переносится. `map` и `odom` для этой работы не публикуются.

## Связи

Каждое ребро публикует только `robot_state_publisher`.
В таблице указаны смещения относительно непосредственного родителя,
ориентации — при нулевых значениях сочленений.

| Parent | Child | xyz, м | rpy, рад | Тип / ось | Топик |
| --- | --- | --- | --- | --- | --- |
| base_link | camera_link | 0.28, 0, 0.38 | 0, 0, 0 | fixed | /tf_static |
| base_link | lidar_link | 0.28, 0, 0.38 | 0, 0, 0 | fixed | /tf_static |
| base_link | imu_link | 0.28, 0, 0.38 | 0, 0, 0 | fixed | /tf_static |
| base_link | front_left_knuckle | 0.40, 0.31, 0 | 0, 0, 0 | revolute / Z | /tf |
| base_link | front_right_knuckle | 0.40, -0.31, 0 | 0, 0, 0 | revolute / Z | /tf |
| front_left_knuckle | front_left_wheel | 0, 0, 0 | 0, 0, 0 | continuous / Y | /tf |
| front_right_knuckle | front_right_wheel | 0, 0, 0 | 0, 0, 0 | continuous / Y | /tf |
| base_link | rear_left_wheel | -0.40, 0.31, 0 | 0, 0, 0 | continuous / Y | /tf |
| base_link | rear_right_wheel | -0.40, -0.31, 0 | 0, 0, 0 | continuous / Y | /tf |

`joint_states` задаёт состояние подвижных сочленений, но не публикует tf.
Для проверки RViz все шесть состояний опубликованы стандартной командой
`ros2 topic pub -r 10 /joint_states sensor_msgs/msg/JointState` из README.
Отдельный `joint_state_publisher` не устанавливался. Без `joint_states`
доступно статическое поддерево камеры, лидара и IMU, но не колёса.

Геометрия цилиндров колёс повёрнута на `pi/2` вокруг X внутри visual/collision;
сами wheel frames не повёрнуты, ось вращения каждого колеса — Y.
Инерциальные числа взяты из SDF; проверяются конечность, положительная масса
и физическая допустимость диагональных значений. Расчёт общего тензора не нужен.
SDF не содержит visual/collision корпусов сенсоров: в URDF они обозначены
небольшими примитивами, не моделирующими реальные измерения.
Сенсорные frames совпадают по SDF, поэтому их обозначения в RViz накладываются.

## Дефект и исправление

Рабочая модель и тесты: коммит `0e06052`.
Коммит `7c0ff95` меняет только parent `lidar_joint` с `base_link` на
`camera_link`, сохраняя offset `(0.28, 0, 0.38)`.
`check_urdf` принимает связное дерево, но `test_sensor_parents_and_offsets`
падает: `camera_link != base_link`. `tf2_echo base_link lidar_link`
показывает ошибочную сумму смещений `(0.56, 0, 0.76)`.
После возврата parent в `base_link` тот же тест проходит, а tf2_echo
показывает `(0.28, 0, 0.38)`, quaternion `(0, 0, 0, 1)`.
Вывод до/после вместе с `view_frames` сохранён в `defect-before.txt`
и `defect-after.txt`. PDF дерева создан инструментом в локальном `log/`;
в Git достаточно его текстового вывода с parent каждого frame.

## Локальная проверка

ROS 2 Lyrical, закреплённый образ из workflow; контейнер `pr05-ros2`,
workspace `/work`, `ROS_DOMAIN_ID=26`, реальное время (`use_sim_time=false`).
После остановки ошибочного publisher исправленная модель запущена командой
`ros2 launch course_description display.launch.py` из установленного пакета.
В `/tf_static` обнаружен ровно один publisher — `robot_state_publisher`.
RViz открыт через X11/WSLg: пользователь подтвердил синий корпус, четыре
чёрных колеса, сенсоры и статусы OK при `Fixed Frame=base_link`.

Предупреждение KDL об инерции корневого `base_link` не мешает публикации tf
и отображению: KDL не использует эту корневую инерцию. Дополнительный dummy
frame не добавлялся. Сообщения RViz об отсутствующих иконках относятся к
образу/курсорам, а не к дереву модели; отображение подтверждено пользователем.
