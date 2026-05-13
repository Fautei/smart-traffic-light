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
        self.declare_parameter('rtsp_url', '')
        self.declare_parameter('frame_id', 'camera')
        self.declare_parameter('camera_name', 'traffic_light_camera')
        self.declare_parameter('calibration_file', '')
        
        self.rtsp_url = self.get_parameter('rtsp_url').get_parameter_value().string_value
        
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        self.camera_name = self.get_parameter('camera_name').get_parameter_value().string_value
        self.calibration_file = self.get_parameter('calibration_file').get_parameter_value().string_value

        # Initialize bridge
        self.bridge = CvBridge()
        
        # Create publishers
        self.publisher_raw = self.create_publisher(Image, '/camera/image_raw', 10)
        self.publisher_info = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        
        # Timer for capture loop
        self.timer = self.create_timer(0.1, self.capture_loop) 
        
        # Camera capture
        self.cap = None
        self.camera_info_msg = None
        
        # Load camera calibration if provided
        if self.calibration_file and os.path.exists(self.calibration_file):
            self.load_camera_calibration(self.calibration_file)

        
        # Open stream
        self.open_stream()


    def load_camera_calibration(self, calibration_file: str):
        """Load camera calibration using OpenCV FileStorage"""

        fs = cv2.FileStorage(calibration_file, cv2.FILE_STORAGE_READ)

        if not fs.isOpened():
            raise RuntimeError(f"Failed to open calibration file: {calibration_file}")

        self.get_logger().info(
            f"Loaded camera calibration from: {calibration_file}"
        )

        self.camera_info_msg = CameraInfo()
        self.camera_info_msg.header.frame_id = self.frame_id

        # Image size
        image_width = int(fs.getNode("image_width").real())
        image_height = int(fs.getNode("image_height").real())

        self.camera_info_msg.width = image_width
        self.camera_info_msg.height = image_height

        # Camera matrix
        camera_matrix = fs.getNode("camera_matrix").mat()

        self.camera_info_msg.k = camera_matrix.flatten().tolist()

        # Distortion coefficients
        dist_coeffs = fs.getNode("dist_coeffs").mat()

        self.camera_info_msg.d = dist_coeffs.flatten().tolist()

        # Distortion model
        distortion_model_node = fs.getNode("distortion_model")

        if not distortion_model_node.empty():
            self.camera_info_msg.distortion_model = distortion_model_node.string()
        else:
            self.camera_info_msg.distortion_model = "plumb_bob"

        fs.release()
                
    def open_stream(self, ffmpeg = False):
        self.get_logger().info(f"Opening url: {self.rtsp_url}")
        if ffmpeg:
            self.cap = cv2.VideoCapture(self.rtsp_url)
        else:
            pipeline = f"rtspsrc location={self.rtsp_url}! decodebin ! videoconvert ! appsink sync=false drop=true" 
            self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            self.get_logger().warn("Failed to open stream. Retrying in 1s...")
            time.sleep(1)
            self.open_stream(ffmpeg=True)

    def capture_loop(self):
        if self.cap is None or not self.cap.isOpened():
            self.get_logger().warn("Stream closed. Reopening...")
            self.open_stream(ffmpeg=True)
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
            self.publisher_info.publish(self.camera_info_msg)

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