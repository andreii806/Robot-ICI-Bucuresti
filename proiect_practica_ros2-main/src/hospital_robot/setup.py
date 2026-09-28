import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'hospital_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Liniile pentru folderele tale:
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.*'))),
        (os.path.join('share', package_name, 'urdf'), glob(os.path.join('urdf', '*.*'))),
        (os.path.join('share', package_name, 'meshes'), glob(os.path.join('meshes', '*.*'))),
        (os.path.join('share', package_name, 'worlds'), glob(os.path.join('worlds', '*.*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='polar',
    maintainer_email='polar@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    # Aici spunem ROS 2 unde sunt scripturile fizice aflate in radacina pachetului:
    scripts=[
        'line_follower_node.py',
        'line_sensor_ground_truth.py',
        'motor_safety_watchdog.py',
        'obstacle_avoidance_node.py',
    
    ],
    entry_points={
        'console_scripts': [
        ],
    },
)