import sys

import rclpy
from rclpy.node import Node

from traffic_light_msgs.msg import TrafficLightState

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
)


class TrafficLightIndicator(QWidget):

    def __init__(self, name="Traffic Light", scale=2.0, parent=None):
        super().__init__(parent)

        self.name = name
        self.scale = scale
        self.current_state = 0

        # Базовые размеры
        self.base_width = 120
        self.base_height = 280

        # Масштабируем окно
        self.setFixedSize(
            int(self.base_width * scale),
            int(self.base_height * scale)
        )

        self.setStyleSheet("background-color: #1a1a1a;")

    def set_state(self, state):
        self.current_state = state
        self.update()

    def paintEvent(self, event):

        s = self.scale

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Все размеры через scale
        housing_width = int(80 * s)
        housing_height = int(220 * s)

        x = (self.width() - housing_width) // 2
        y = int(20 * s)

        circle_radius = int(25 * s)
        vertical_spacing = int(5 * s)

        painter.setPen(QColor("#000000"))
        painter.setBrush(QColor("#333333"))

        painter.drawRoundedRect(
            x,
            y,
            housing_width,
            housing_height,
            int(10 * s),
            int(10 * s)
        )

        center_x = x + housing_width // 2

        red_y = y + circle_radius + vertical_spacing
        self._draw_circle(painter, center_x, red_y, circle_radius, 0)

        yellow_y = red_y + 2 * (circle_radius + vertical_spacing)
        self._draw_circle(painter, center_x, yellow_y, circle_radius, 1)

        green_y = yellow_y + 2 * (circle_radius + vertical_spacing)
        self._draw_circle(painter, center_x, green_y, circle_radius, 2)

    def _draw_circle(self, painter, center_x, center_y, radius, light_index):

        colors = {
            0: (QColor("#ff0000"), QColor("#880000")),
            1: (QColor("#ffff00"), QColor("#888800")),
            2: (QColor("#00ff00"), QColor("#008800")),
        }

        on_color, off_color = colors[light_index]

        if light_index == self.current_state:
            painter.setBrush(on_color)
            painter.setPen(on_color)
        else:
            painter.setBrush(off_color)
            painter.setPen(off_color)

        painter.drawEllipse(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2
        )


class TrafficLightIndicatorNode(Node):
    """
    ROS2 node that subscribes to traffic light topics and displays indicators.
    Creates separate windows for each traffic light.
    """

    def __init__(self):
        super().__init__('traffic_light_indicator')

        # Parameters
        self.declare_parameter('tl_topic', '/traffic_light_1/state')

        tl_topic = self.get_parameter('tl_topic').value

        # Subscribers
        self.tl_sub = self.create_subscription(
            TrafficLightState,
            tl_topic,
            self.tl_callback,
            10
        )

        # Current states
        self.tl_state = 0  # Default RED


        self.get_logger().info('Traffic Light Indicator node started')

    def tl_callback(self, msg):
        """Callback for traffic light 1 state."""
        self.tl_state = msg.state
        if hasattr(self, 'indicator') and self.indicator:
            self.indicator.set_state(msg.state)
        self.get_logger().debug(f'Traffic Light state: {msg.state}')




def main():
    rclpy.init()

    app = QApplication(sys.argv)

    # Create ROS2 node
    node = TrafficLightIndicatorNode()

    # Create separate windows for each traffic light
    node.indicator = TrafficLightIndicator("Traffic Light")
    node.indicator.show()

    # Timer for ROS spinning
    ros_timer = QTimer()
    ros_timer.timeout.connect(lambda: rclpy.spin_once(node, timeout_sec=0.001))
    ros_timer.start(10)

    sys.exit(app.exec())

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()