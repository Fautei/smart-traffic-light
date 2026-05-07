import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    Detection2DArray,
    Detection2D,
    ObjectHypothesisWithPose,
    BoundingBox2D
)
from cv_bridge import CvBridge
from ultralytics import YOLO
import numpy as np
import cv2


class ObjectDetector(Node):
    def __init__(self):
        super().__init__('object_detector')

        # params
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('model_path', 'yolov8n.pt')

        self.conf_thres = self.get_parameter('confidence_threshold').value
        self.image_topic = self.get_parameter('image_topic').value
        model_path = self.get_parameter('model_path').value

        # bridge
        self.bridge = CvBridge()

        # Ultralytics model
        self.model = YOLO(model_path)

        # pub/sub
        self.det_pub = self.create_publisher(
            Detection2DArray,
            '/detections',
            10
        )

        self.debug_pub = self.create_publisher(
            Image,
            '/camera/image_detections',
            10
        )

        self.image_sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )

        self.get_logger().info("Ultralytics YOLO detector ready")

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")

            # 🔥 INFERENCE (всё внутри — preprocess + NMS + decode)
            results = self.model.predict(
                source=frame,
                conf=self.conf_thres,
                verbose=False
            )

            result = results[0]

            # annotated image
            annotated = result.plot()

            # (optional) publish debug image
            self.debug_pub.publish(
                self.bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
            )

            det_array = Detection2DArray()
            det_array.header = msg.header

            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])

                    det = Detection2D()
                    det.header = msg.header

                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    w = (x2 - x1)
                    h = (y2 - y1)

                    det.bbox = BoundingBox2D()
                    det.bbox.center.position.x = float(cx)
                    det.bbox.center.position.y = float(cy)
                    det.bbox.center.theta = 0.0

                    det.bbox.size_x = float(w)
                    det.bbox.size_y = float(h)

                    hypothesis = ObjectHypothesisWithPose()
                    hypothesis.hypothesis.class_id = str(cls)
                    hypothesis.hypothesis.score = float(conf)

                    det.results.append(hypothesis)

                    det_array.detections.append(det)

            self.det_pub.publish(det_array)

        except Exception as e:
            self.get_logger().error(f"Detection error: {e}")


def main():
    rclpy.init()
    node = ObjectDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()