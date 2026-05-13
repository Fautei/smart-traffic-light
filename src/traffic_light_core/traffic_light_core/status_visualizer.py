import sys
from collections import deque

import cv2
import numpy as np

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray
from std_msgs.msg import Int32MultiArray

from cv_bridge import CvBridge

from traffic_light_msgs.msg import PolygonPoints

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QFont,
)
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
)


class ImageWidget(QLabel):
    """
    Widget for displaying OpenCV images.
    """

    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background-color: black;")

    def set_cv_image(self, frame):
        """
        Convert OpenCV image to Qt image.
        """

        if frame is None:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        image = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(image)

        self.setPixmap(
            pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )


class StatusVisualizer(Node, QMainWindow):
    """
    Status Visualizer using PySide6.
    """

    def __init__(self):
        Node.__init__(self, 'status_visualizer')
        QMainWindow.__init__(self)

        # Parameters
        self.declare_parameter('detection_topic', '/detections_1')
        self.declare_parameter('polygon_topic', '/polygon_config/polygon')
        self.declare_parameter('image_topic', '/camera_1/image_detections')
        self.declare_parameter('count_topic', '/traffic_counter/counts')
        self.declare_parameter('max_history', 60)

        self.detection_topic = self.get_parameter('detection_topic').value
        self.polygon_topic = self.get_parameter('polygon_topic').value
        self.image_topic = self.get_parameter('image_topic').value
        self.count_topic = self.get_parameter('count_topic').value
        self.max_history = self.get_parameter('max_history').value

        # ROS
        self.bridge = CvBridge()

        # Data
        self.current_frame = None
        self.detections = []
        self.polygon_points = []

        self.history_minutes = 10
        self.sample_rate_hz = 1

        self.max_history = (
            self.history_minutes * 60 * self.sample_rate_hz
        )

        self.classes = [
            'car',
            'truck',
            'bus',
            'motorcycle',
            'person'
        ]

        self.history = {
            cls: deque([0] * self.max_history,
                    maxlen=self.max_history)
            for cls in self.classes
        }

        self.current_counts = {
            cls: 0
            for cls in self.classes
        }

        self.history_timer = QTimer()
        self.history_timer.timeout.connect(
            self.update_history
        )
        self.history_timer.start(1000)  # 1 sec

        # Subscribers
        self.image_sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )

        self.detection_sub = self.create_subscription(
            Detection2DArray,
            self.detection_topic,
            self.detection_callback,
            10
        )

        self.polygon_sub = self.create_subscription(
            PolygonPoints,
            self.polygon_topic,
            self.polygon_callback,
            10
        )

        self.count_sub = self.create_subscription(
            Int32MultiArray,
            self.count_topic,
            self.count_callback,
            10
        )

        # UI
        self.setWindowTitle("Traffic Status Visualizer")
        self.resize(1400, 900)

        self.setup_ui()

        # Timers
        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(self.spin_ros)
        self.ros_timer.start(10)

        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(33)

        self.get_logger().info("Status Visualizer started")

    def update_history(self):
        """
        Save current counts into history.
        """

        for cls in self.classes:

            value = self.current_counts.get(cls, 0)

            self.history[cls].append(value)

    def setup_ui(self):
        """
        Create GUI.
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Tabs
        self.tabs = QTabWidget()

        # Frame tab
        self.frame_widget = QWidget()
        self.frame_layout = QVBoxLayout()
        self.frame_widget.setLayout(self.frame_layout)

        self.frame_label = ImageWidget()
        self.frame_layout.addWidget(self.frame_label)

        self.tabs.addTab(self.frame_widget, "Frame")

        # Plot tab
        self.plot_widget = QWidget()
        self.plot_layout = QVBoxLayout()
        self.plot_widget.setLayout(self.plot_layout)

        self.plot_label = ImageWidget()
        self.plot_layout.addWidget(self.plot_label)

        self.tabs.addTab(self.plot_widget, "Plots")

        main_layout.addWidget(self.tabs)

        # Bottom controls
        controls_layout = QHBoxLayout()

        self.info_label = QLabel("Ready")

        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)

        controls_layout.addWidget(self.info_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.quit_button)

        main_layout.addLayout(controls_layout)

    def spin_ros(self):
        """
        ROS spin once.
        """

        rclpy.spin_once(self, timeout_sec=0.001)

    def image_callback(self, msg: Image):
        """
        Receive image.
        """

        try:
            self.current_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")

        except Exception as e:
            self.get_logger().error(
                f"Image conversion failed: {e}"
            )

    def polygon_callback(self, msg: PolygonPoints):
        """
        Receive polygon.
        """

        self.polygon_points = []

        for point in msg.points:
            self.polygon_points.append(
                (point.x, point.y)
            )

    def detection_callback(self, msg: Detection2DArray):
        """
        Receive detections.
        """

        self.detections = []

        counts = {
            cls: 0
            for cls in self.classes
        }

        for detection in msg.detections:

            if len(detection.results) == 0:
                continue

            result = detection.results[0]

            cls = result.hypothesis.class_id
            score = result.hypothesis.score

            bbox = detection.bbox

            self.detections.append({
                'class': cls,
                'confidence': score,
                'bbox': {
                    'x': bbox.center.position.x,
                    'y': bbox.center.position.y,
                    'w': bbox.size_x,
                    'h': bbox.size_y,
                }
            })

            if cls not in counts:
                counts[cls] = 0

            counts[cls] += 1

        self.current_counts = counts

    def count_callback(self, msg: Int32MultiArray):
        """
        Receive counts.
        """

        pass

    def draw_polygon(self, frame):
        """
        Draw polygon.
        """

        if len(self.polygon_points) < 3:
            return

        pts = np.array(
            self.polygon_points,
            dtype=np.int32
        )

        cv2.polylines(
            frame,
            [pts],
            True,
            (0, 255, 0),
            2
        )

    def draw_detections(self, frame):
        """
        Draw detections.
        """

        for det in self.detections:

            bbox = det['bbox']

            x1 = int(bbox['x'] - bbox['w'] / 2)
            y1 = int(bbox['y'] - bbox['h'] / 2)

            x2 = int(bbox['x'] + bbox['w'] / 2)
            y2 = int(bbox['y'] + bbox['h'] / 2)

            cls = det['class']
            conf = det['confidence']

            # Colors
            if cls == 'person':
                color = (255, 100, 100)
            else:
                color = (100, 255, 100)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            label = f"{cls} {conf:.2f}"

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

    def create_plot_image(self, width, height):
        """
        Create realtime scrolling history plots.
        """

        plot = np.ones(
            (height, width, 3),
            dtype=np.uint8
        ) * 25

        num_classes = len(self.classes)

        if num_classes == 0:
            return plot

        section_height = height // num_classes

        colors = {
            'car': (0, 255, 0),
            'truck': (0, 200, 255),
            'bus': (255, 200, 0),
            'motorcycle': (255, 0, 255),
            'person': (0, 100, 255),
        }

        for idx, cls in enumerate(self.classes):

            y_top = idx * section_height
            y_bottom = y_top + section_height

            history = list(self.history[cls])

            if len(history) < 2:
                continue

            max_value = max(max(history), 1)

            # Background area
            cv2.rectangle(
                plot,
                (0, y_top),
                (width, y_bottom),
                (35, 35, 35),
                -1
            )

            # Grid
            for g in range(5):

                gy = y_top + int(
                    g * section_height / 5
                )

                cv2.line(
                    plot,
                    (0, gy),
                    (width, gy),
                    (60, 60, 60),
                    1
                )

            color = colors.get(
                cls,
                (200, 200, 200)
            )

            # Draw scrolling bars
            step_x = width / self.max_history

            for i, value in enumerate(history):

                x = int(i * step_x)

                normalized = value / max_value

                bar_height = int(
                    normalized * (section_height - 40)
                )

                cv2.line(
                    plot,
                    (x, y_bottom - 20),
                    (x, y_bottom - 20 - bar_height),
                    color,
                    2
                )

            # Current value
            current_value = history[-1]

            cv2.putText(
                plot,
                f"{cls}: {current_value}",
                (10, y_top + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

            # Max label
            cv2.putText(
                plot,
                f"max {max_value}",
                (width - 120, y_top + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (180, 180, 180),
                1
            )

        # Timeline label
        cv2.putText(
            plot,
            f"Last {self.history_minutes} min",
            (width - 220, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        return plot

    def update_display(self):
        """
        Update GUI.
        """

        if self.current_frame is None:
            return

        frame = self.current_frame.copy()

        self.draw_polygon(frame)
        self.draw_detections(frame)

        # Frame tab
        self.frame_label.set_cv_image(frame)

        # Plot tab

        size = self.plot_label.size()
        w = size.width()
        h = size.height()

        plot = self.create_plot_image(w, h)

        self.plot_label.set_cv_image(plot)

        self.info_label.setText(
            f"Detections: {len(self.detections)} | "
            f"Polygon points: {len(self.polygon_points)}"
        )

    def keyPressEvent(self, event):
        """
        Keyboard shortcuts.
        """

        key = event.key()

        if key == Qt.Key_Q or key == Qt.Key_Escape:
            self.close()

        elif key == Qt.Key_Tab:

            current = self.tabs.currentIndex()

            self.tabs.setCurrentIndex(
                1 - current
            )

    def closeEvent(self, event):
        """
        Cleanup.
        """

        self.get_logger().info(
            "Closing Status Visualizer"
        )

        self.destroy_node()

        rclpy.shutdown()

        event.accept()


def main():

    rclpy.init()

    app = QApplication(sys.argv)

    window = StatusVisualizer()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()