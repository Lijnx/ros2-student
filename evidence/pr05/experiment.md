# ПР05: наблюдения

Среда приведена в `environment.txt`, сборка в `build.txt`, полный прогон тестов
в `tests.txt`. Исходная несовместимая конфигурация находится в коммите
`0664085`; исправленный launch — в `a51a499`.

## Живой поток

Один глобальный turtlesim; `/robot_a/{patrol,pose_relay,pose_subscriber}`.
В `qos-before.txt` видны совпадающие тип и имя, BEST_EFFORT издателя,
RELIABLE подписчика, предупреждение RELIABILITY и `exit=124` у echo.
В `live-before.log` собственный читатель всё время пишет `received=0`.
При `record=false` recorder и каталог bag отсутствовали.

После перезапуска с `subscriber_reliability:=best_effort record:=true`
читатель и recorder используют BEST_EFFORT; echo получил Pose с `exit=0`.
`qos-after.txt` показывает действующий remap команды и разные последовательные
позы turtlesim. В `live-after.log` счётчик читателя растёт.

## Одна запись и replay

Recorder завершён штатно вместе с живым launch. Скопирована его metadata.
В MCAP ровно один топик `/robot_a/sensor_pose`, 1264 сообщения,
длительность 20.278187595 с. Вывод `ros2 bag info` включён в `qos-after.txt`.

При replay живые ноды отсутствуют. Единственный publisher — `rosbag2_player`,
его BEST_EFFORT задан через `config/qos-overrides.yaml` и виден в verbose.
На одной непрерывно повторяемой записи запускались два профиля читателя:

| Проверка | reliable | best_effort |
| --- | --- | --- |
| Callback приложения | 0 | больше 0 |
| CLI echo | timeout, 124 | Pose, 0 |

Содержимое bag не менялось: до и после обоих чтений SHA-256 MCAP равен
`976f2fd831f979a42cf8545b2ebb78c4bc2ad75c00edcc70f39e0c1bc3e2d8bd`.
Логи собственных читателей — `replay-reliable.log` и
`replay-best_effort.log`, player — `replay.log`.

Максимальный залогированный счётчик live-after — 1239, replay-best_effort — 434.
Они не равны полному числу записанных сообщений: интервалы работы читателей
отличаются от интервала recorder, логирование идёт раз в секунду.
Это не метрика потерь и не требование получить весь bag.

## Повторение

Из корня workspace после подключения ROS/overlay и в свободном домене:

```bash
export ROS_DOMAIN_ID=25
python3 scripts/pr05_experiment.py
```

Новый опыт сохраняется в свежий каталог `log/pr05-<дата-время>`, не поверх
этой сдачи. Там создаётся одна новая запись, общая для его before/after.
Сохранённый локально bag этой сдачи исключён из Git.

CI ограничен сборкой, функциональными тестами пакетов и checker.
Живой опыт и replay проверены локально; исходные логи и metadata сохранены.
Необязательный launch-тест с turtlesim и записью из набора тестов удалён.
Текущий результат тестов приведён в `tests.txt`; два skip относятся к
прежним copyright-тестам. Старые evidence ПР01–ПР04 не изменялись.
