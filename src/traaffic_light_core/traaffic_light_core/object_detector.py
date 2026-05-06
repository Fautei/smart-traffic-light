"""
Object detector node using Ultralytics YOLOv8.
Publishes detection results using standard ROS2 sensor_msgs.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, RegionOfInterest
from std_msgs.msg import Header
from cv_bridge import CvBridge
import cv2
import torch
from typing import List, Dict, Any
import yaml
import os

from .traffic_light_logic import TrafficLightState


class ObjectDetector(Node):
    """Object detector node using YOLOv8 for vehicle detection."""
    
    def __init__(self):
        super().__init__('object_detector')
        
        # Declare parameters
        self.declare_parameter('model_path', '')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('classes_to_detect', ['car', 'truck', 'bus'])
        self.declare_parameter('publish_detections', True)
        self.declare_parameter('draw_detections', False)
        self.declare_parameter('detection_topic', '/detections')
        self.declare_parameter('image_topic', '/camera/image_raw')
        
        # Get parameters
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        self.confidence_threshold = self.get_parameter('confidence_threshold').get_parameter_value().double_value
        classes_to_detect = self.get_parameter('classes_to_detect').get_parameter_value().string_array_value
        self.publish_detections = self.get_parameter('publish_detections').get_parameter_value().bool_value
        self.draw_detections = self.get_parameter('draw_detections').get_parameter_value().bool_value
        self.detection_topic = self.get_parameter('detection_topic').get_parameter_value().string_value
        self.image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        
        # Initialize bridge
        self.bridge = CvBridge()
        
        # Load YOLO model
        if model_path:
            try:
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=False)
                self.get_logger().info(f"Loaded YOLO model from: {model_path}")
            except Exception as e:
                self.get_logger().error(f"Failed to load YOLO model: {e}")
                self.model = None
        else:
            # Load default YOLOv8 model
            try:
                from ultralytics import YOLO
                self.model = YOLO('yolov8n.pt')
                self.get_logger().info("Loaded default YOLOv8 model")
            except Exception as e:
                self.get_logger().error(f"Failed to load YOLO model: {e}")
                self.model = None
        
        # Map class names to indices
        self.classes_to_detect_ids = []
        if self.model:
            class_names = self.model.names if hasattr(self.model, 'names') else self.model.model.names
            for class_name in classes_to_detect:
                if class_name in class_names:
                    self.classes_to_detect_ids.append(list(class_names.values()).index(class_name))
                    self.get_logger().info(f"Class '{class_name}' mapped to ID: {self.classes_to_detect_ids[-1]}")
        
        # Create publishers
        self.detections_pub = self.create_publisher(Image, self.detection_topic, 10)
        
        # Create subscriber
        self.image_sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )
        
        self.get_logger().info("Object detector initialized")
    
    def image_callback(self, msg: Image):
        """Process incoming image and detect objects."""
        if self.model is None:
            return
        
        try:
            # Convert image to numpy array
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # Run inference
            results = self.model(frame)
            
            # Process results
            detections = []
            if results and len(results) > 0:
                for result in results:
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        for box in result.boxes:
                            cls_id = int(box.cls.item())
                            conf = box.conf.item()
                            
                            # Check if class is in our detection list
                            if self.classes_to_detect_ids and cls_id not in self.classes_to_detect_ids:
                                continue
                            
                            if conf >= self.confidence_threshold:
                                # Get bounding box coordinates
                                xyxy = box.xyxy[0]
                                x1, y1, x2, y2 = int(xyxy[0].item()), int(xyxy[1].item()), \
                                               int(xyxy[2].item()), int(xyxy[3].item())
                                
                                detections.append({
                                    'class_id': cls_id,
                                    'class_name': self.model.names.get(cls_id, 'unknown'),
                                    'confidence': conf,
                                    'x1': x1,
                                    'y1': y1,
                                    'x2': x2,
                                    'y2': y2,
                                    'width': x2 - x1,
                                    'height': y2 - y1
                                })
            
            # Publish detections if enabled
            if self.publish_detections and detections:
                self.publish_detection_image(frame, detections, msg.header)
            
        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")
    
    def publish_detection_image(self, frame: cv2.Mat, detections: List[Dict], header: Header):
        """Publish image with drawn detections."""
        if not self.draw_detections:
            return
        
        # Draw detections on frame
        frame_with_detections = frame.copy()
        
        for det in detections:
            # Draw bounding box
            cv2.rectangle(frame_with_detections, 
                         (det['x1'], det['y1']), 
                         (det['x2'], det['y2']), 
                         (0, 255, 0), 2)
            
            # Draw label
            label = f"{det['class_name']}: {det['confidence']:.2f}"
            cv2.putText(frame_with_detections, label,
                       (det['x1'], det['y1'] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Convert to ROS message
        msg = self.bridge.cv2_to_imgmsg(frame_with_detections, encoding='bgr8')
        msg.header = header
        self.detections_pub.publish(msg)


def main():
    rclpy.init()
    node = ObjectDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()