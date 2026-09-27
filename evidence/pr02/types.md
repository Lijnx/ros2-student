# Типы сообщений ПР02

| Топик | Тип | Назначение |
| --- | --- | --- |
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | Команда скорости для `/turtlesim` |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | Положение и текущие скорости черепахи |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Намеренно ошибочное полное имя в опыте |

`ros2 interface show geometry_msgs/msg/Twist` подтверждает два вектора:
`linear` и `angular`, каждый с полями `x`, `y`, `z` типа `float64`.
В двумерном turtlesim использованы `linear.x=1.0` для движения вперёд
и `angular.z=0.5` для поворота. Остальные компоненты остались нулевыми.
Фактическое описание типа — в [twist-interface.txt](twist-interface.txt).

Фактический тип позы получен через `ros2 topic type /turtle1/pose` и
сохранён в [pose-type.txt](pose-type.txt). Он зависит от дистрибутива;
на использованном Lyrical это `turtlesim_msgs/msg/Pose`.
