import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge
import cv2
import time
import numpy as np

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.declare_parameter('gstreamer_pipeline', '')
        self.pipeline = self.get_parameter('gstreamer_pipeline').get_parameter_value().string_value

        if not self.pipeline:
            self.get_logger().error("No GStreamer pipeline provided. Set 'gstreamer_pipeline' parameter.")
            rclpy.shutdown()
            return

        self.bridge = CvBridge()
        self.publisher_raw = self.create_publisher(Image, '/camera/image_raw', 10)
        self.timer = self.create_timer(0.05, self.capture_loop)

        self.cap = None
        self.open_stream()

    def open_stream(self):
        self.get_logger().info(f"Opening GStreamer pipeline: {self.pipeline}")
        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER) #, cv2.CAP_GSTREAMER
        if not self.cap.isOpened():
            self.get_logger().warn("Failed to open stream. Retrying in 1s...")
            time.sleep(1)
            self.open_stream()

    def capture_loop(self):
        if self.cap is None or not self.cap.isOpened():
            self.get_logger().warn("Stream closed. Reopening...")
            self.open_stream()
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.get_logger().warn("Failed to read frame. Reopening stream...")
            self.cap.release()
            self.cap = None
            time.sleep(1)
            return
        
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.publisher_raw.publish(msg)

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()

def main():
    rclpy.init()
    node = CameraNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()