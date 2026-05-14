import sys
import cv2
import numpy as np

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import Bool

from traffic_light_msgs.msg import PolygonPoints, PolygonPoint

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


class ImageLabel(QLabel):
    """
    QLabel with mouse support for polygon point selection.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setAlignment(Qt.AlignCenter)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.parent_window is not None:
                self.parent_window.handle_mouse_click(event.position().x(),
                                                      event.position().y())


class PolygonConfigurator(Node, QMainWindow):
    """
    Polygon Configurator with PySide6 GUI
    """

    def __init__(self):
        Node.__init__(self, 'polygon_configurator')
        QMainWindow.__init__(self)

        # Parameters
        self.declare_parameter('image_topic', '/camera_1/image_raw')
        self.declare_parameter('polygon_topic', '/polygon_config/polygon')

        self.image_topic = self.get_parameter('image_topic').value
        self.polygon_topic = self.get_parameter('polygon_topic').value

        # ROS
        self.bridge = CvBridge()

        self.polygon_pub = self.create_publisher(
            PolygonPoints,
            self.polygon_topic,
            10
        )

        self.image_sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )

        # Data
        self.current_frame = None
        self.points = []

        # GUI
        self.setWindowTitle("Polygon Configurator")
        self.resize(1280, 720)

        self.setup_ui()

        # Timers
        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(self.spin_ros)
        self.ros_timer.start(10)

        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(33)

        self.get_logger().info("Polygon Configurator started")

    def setup_ui(self):
        """
        Create UI
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Image
        self.image_label = ImageLabel(self)
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.image_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.confirm_button = QPushButton("Confirm (C)")
        self.confirm_button.clicked.connect(self.confirm_polygon)

        self.reset_button = QPushButton("Reset (R)")
        self.reset_button.clicked.connect(self.reset_polygon)

        self.quit_button = QPushButton("Quit (Q)")
        self.quit_button.clicked.connect(self.close)

        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.quit_button)

        main_layout.addLayout(button_layout)

        # Info
        self.info_label = QLabel(
            "Left click: Add point | C: Confirm | R: Reset | Q: Quit"
        )
        self.info_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(self.info_label)

    def spin_ros(self):
        """
        ROS spin once
        """
        rclpy.spin_once(self, timeout_sec=0.001)

    def image_callback(self, msg: Image):
        """
        Receive ROS image
        """
        try:
            self.current_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"Image conversion failed: {e}")

    def update_display(self):
        """
        Update displayed frame
        """
        if self.current_frame is None:
            return

        frame = self.current_frame.copy()

        # Draw polygon
        self.draw_polygon(frame)

        # Convert OpenCV -> Qt
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        qt_image = QImage(
            rgb_frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(qt_image)

        self.image_label.setPixmap(
            pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

        self.info_label.setText(
            f"Points: {len(self.points)} | "
            "Left click: Add point | C: Confirm | R: Reset | Q: Quit"
        )

    def draw_polygon(self, frame):
        """
        Draw polygon on frame
        """

        if len(self.points) == 0:
            return

        # Draw lines
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]

            cv2.line(
                frame,
                (int(p1.x), int(p1.y)),
                (int(p2.x), int(p2.y)),
                (0, 255, 0),
                2
            )

        # Draw points
        for idx, point in enumerate(self.points):
            x = int(point.x)
            y = int(point.y)

            cv2.circle(frame, (x, y), 6, (0, 255, 0), -1)

            cv2.putText(
                frame,
                str(idx),
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    def handle_mouse_click(self, label_x, label_y):
        """
        Convert QLabel coordinates -> image coordinates
        """

        if self.current_frame is None:
            return

        pixmap = self.image_label.pixmap()

        if pixmap is None:
            return

        label_width = self.image_label.width()
        label_height = self.image_label.height()

        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        offset_x = (label_width - pixmap_width) / 2
        offset_y = (label_height - pixmap_height) / 2

        img_x = label_x - offset_x
        img_y = label_y - offset_y

        if img_x < 0 or img_y < 0:
            return

        scale_x = self.current_frame.shape[1] / pixmap_width
        scale_y = self.current_frame.shape[0] / pixmap_height

        real_x = int(img_x * scale_x)
        real_y = int(img_y * scale_y)

        if (
            real_x < 0
            or real_y < 0
            or real_x >= self.current_frame.shape[1]
            or real_y >= self.current_frame.shape[0]
        ):
            return

        point = PolygonPoint()
        point.x = float(real_x)
        point.y = float(real_y)

        self.points.append(point)

        self.get_logger().info(
            f"Added point: ({real_x}, {real_y})"
        )

    def confirm_polygon(self):
        """
        Publish polygon
        """

        if len(self.points) < 3:
            self.get_logger().warning(
                "Polygon must contain at least 3 points"
            )
            return

        polygon_msg = PolygonPoints()
        polygon_msg.points = self.points.copy()

        self.polygon_pub.publish(polygon_msg)

        self.get_logger().info(
            f"Polygon published: {len(self.points)} points"
        )

    def reset_polygon(self):
        """
        Reset polygon
        """

        self.points.clear()

        self.get_logger().info("Polygon reset")

    def keyPressEvent(self, event):
        """
        Keyboard shortcuts
        """

        key = event.key()

        if key == Qt.Key_C:
            self.confirm_polygon()

        elif key == Qt.Key_R:
            self.reset_polygon()

        elif key == Qt.Key_Q or key == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        """
        Cleanup
        """

        self.get_logger().info("Closing Polygon Configurator")

        self.destroy_node()
        rclpy.shutdown()

        event.accept()


def main():
    rclpy.init()

    app = QApplication(sys.argv)

    window = PolygonConfigurator()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()