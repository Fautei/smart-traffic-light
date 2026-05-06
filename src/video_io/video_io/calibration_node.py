import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
import os

class CalibrationNode(Node):
    def __init__(self):
        super().__init__('calibration_node')

        self.declare_parameter('calibration_file', '')
        self.declare_parameter('roi', [0, 0, 0, 0])  # top, bottom, left, right

        calib_file = self.get_parameter('calibration_file').get_parameter_value().string_value
        self.roi = self.get_parameter('roi').get_parameter_value().integer_array_value

        if not os.path.isfile(calib_file):
            self.get_logger().error(f"Calibration file not found: {calib_file}")
            rclpy.shutdown()
            return

        self.get_logger().info(f"Loading calibration from: {calib_file}")
        with np.load(calib_file) as data:
            self.camera_matrix = data["camera_matrix"]
            self.dist_coeffs = data["dist_coeffs"]

        self.bridge = CvBridge()
        self.map1 = None
        self.map2 = None
        self.frame_size_initialized = False

        self.subscription = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        self.publisher = self.create_publisher(Image, '/camera/image_remapped/raw', 10)


    def apply_roi(self, frame):
        top, bottom, left, right = self.roi
        h, w, _ = frame.shape

        # Convert negative indices
        if bottom <= 0:
            bottom = h + bottom
        if right <= 0:
            right = w + right

        return frame[top:bottom, left:right]
 
    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"CVBridge error: {e}")
            return

        h, w = frame.shape[:2]

        if not self.frame_size_initialized:
            self.get_logger().info(f"Initializing undistortion maps for resolution: {w}x{h}")
            new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
                self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h)
            )

            self.map1, self.map2 = cv2.initUndistortRectifyMap(
                self.camera_matrix, self.dist_coeffs, None, new_camera_matrix, (w, h), cv2.CV_16SC2
            )
            self.frame_size_initialized = True

        undistorted = cv2.remap(frame, self.map1, self.map2, interpolation=cv2.INTER_LINEAR)
        undistorted = self.apply_roi(undistorted)

        #uh, uw = undistorted.shape[:2]
        #undistorted = cv2.resize(undistorted, (uw // 2,uh // 2))

        self.publisher.publish(self.bridge.cv2_to_imgmsg(undistorted, encoding='bgr8'))

def main():
    rclpy.init()
    node = CalibrationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()