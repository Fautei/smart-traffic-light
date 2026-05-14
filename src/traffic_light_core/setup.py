from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'traffic_light_core'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
        'opencv-python',
        'PyYAML',
        'PySide6'
    ],
    zip_safe=True,
    maintainer='Fautei',
    maintainer_email='maxim.6926@gmail.com',
    description='Package for smart traffic light system with YOLO object detection',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'object_detector = traffic_light_core.object_detector:main',
            'traffic_light_logic = traffic_light_core.traffic_light_logic:main',
            'traffic_light_indicator = traffic_light_core.traffic_light_indicator:main',
            'polygon_configurator = traffic_light_core.polygon_configurator:main',
            'traffic_counter = traffic_light_core.traffic_counter:main',
            'status_visualizer = traffic_light_core.status_visualizer:main',
        ],
    },
)
