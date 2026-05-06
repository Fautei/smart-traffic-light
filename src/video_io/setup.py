from setuptools import find_packages, setup

package_name = 'video_io'

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
        'cv_bridge',
        'sensor_msgs',
    ],
    zip_safe=True,
    maintainer='maxim',
    maintainer_email='maxim.6926@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_node = video_io.camera_node:main',
            'calibration_node = video_io.calibration_node:main',
        ]
    },
)
