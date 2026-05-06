import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import time
import numpy as np
import yaml
import os
from pathlib import Path

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        # Declare parameters
        self.declare_parameter('gstreamer_pipeline', '')
        self.declare_parameter('camera_info_url', '')
        self.declare_parameter('frame_id', 'camera')
        self.declare_parameter('camera_name', 'traffic_light_camera')
        self.declare_parameter('calibration_file', '')
        
        self.pipeline = self.get_parameter('gstreamer_pipeline').get_parameter_value().string_value
        self.camera_info_url = self.get_parameter('camera_info_url').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        self.camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        self.calibration_file = self.get_parameter('calibration_file').get_parameter_value().string_value

        # Initialize bridge
        self.bridge = CvBridge()
        
        # Create publishers
        self.publisher_raw = self.create_publisher(Image, '/camera/image_raw', 10)
        self.publisher_info = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        
        # Timer for capture loop
        self.timer = self.create_timer(0.033, self.capture_loop)  # ~30 FPS
        
        # Camera capture
        self.cap = None
        self.camera_info_msg = None
        
        # Load camera calibration if provided
        if self.calibration_file and os.path.exists(self.calibration_file):
            self.load_camera_calibration(self.calibration_file)
        elif self.camera_info_url:
            self.load_camera_info_from_url(self.camera_info_url)
        
        # Open stream
        self.open_stream()

    def load_camera_calibration(self, calibration_file: str):
        """Load camera calibration from YAML file"""
        try:
            with open(calibration_file, 'r') as f:
                cal_data = yaml.safe_load(f)
            
            self.get_logger().info(f"Loaded camera calibration from: {calibration_file}")
            
            # Create CameraInfo message
            self.camera_info_msg = CameraInfo()
            self.camera_info_msg.header.frame_id = self.frame_id
            self.camera_info_msg.height = cal_data.get('image_height', 480)
            self.camera_info_msg.width = cal_data.get('image_width', 640)
            
            # Distortion coefficients
            self.camera_info_msg.distortion_model = cal_data.get('distortion_model', 'plumb_bob')
            D = cal_data.get('distortion_coefficients', {}).get('data', [0.0, 0.0, 0.0, 0.0, 0.0])
            self.camera_info_msg.d = list(D)
            
            # Camera matrix
            K = cal_data.get('camera_matrix', {}).get('data', [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])
            self.camera_info_msg.k = list(K)
            
            # Rectification matrix
            R = cal_data.get('rectification_matrix', {}).get('data', [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])
            self.camera_info_msg.r = list(R)
            
            # Projection matrix
            P = cal_data.get('projection_matrix', {}).get('data', [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
            self.camera_info_msg.p = list(P)
            
        except Exception as e:
            self.get_logger().error(f"Failed to load calibration file: {e}")

    def load_camera_info_from_url(self, camera_info_url: str):
        """Load camera info from ROS camera_info URL format"""
        try:
            # Parse URL format: file://path/to/calibration.yaml
            if camera_info_url.startswith('file://'):
                path = camera_info_url[7:]
                self.load_camera_calibration(path)
            else:
                self.get_logger().warn(f"Unsupported URL format: {camera_info_url}")
        except Exception as e:
            self.get_logger().error(f"Failed to load camera info from URL: {e}")

    def open_stream(self):
        self.get_logger().info(f"Opening GStreamer pipeline: {self.pipeline}")
        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
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
        
        # Create image message
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.frame_id = self.frame_id
        self.publisher_raw.publish(msg)
        
        # Publish camera info if available
        if self.camera_info_msg is not None:
            info_msg = self.camera_info_msg.__copy__()
            info_msg.header.stamp = msg.header.stamp
            self.publisher_info.publish(info_msg)

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