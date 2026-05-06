"""
Package for smart traffic light system with YOLO object detection.
"""

from .object_detector import ObjectDetector
from .traffic_light_logic import TrafficLightLogic, TrafficLightState

__all__ = ['ObjectDetector', 'TrafficLightLogic', 'TrafficLightState']