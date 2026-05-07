# Установка

Что бы не создавать себе еще больше ненужных проблем рекомендуется использовать ubuntu 22.04/24.04 

- Установить ros2 humble/kilted https://docs.ros.org/en/humble/Installation.html
- Установить ultralytics
- source /opt/ros/kilted/setup.bash
- colcon build 
- source install/local_setup.bash 
- ros2 launch traaffic_light_launch traaffic_light_launch.py 

В лаунч файле нужно настроить rtsp url для своих камер

После этого все должно работать

(Пока что просто базовое определение объектов транспорта с передачей этой информации в ноды принятия решений)