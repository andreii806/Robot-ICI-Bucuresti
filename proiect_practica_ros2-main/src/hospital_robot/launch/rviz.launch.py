import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'hospital_robot'
    pkg_share = get_package_share_directory(pkg_name)
    
    urdf_path = os.path.join(pkg_share, 'urdf', 'ansamblu_final.urdf')
    
    with open(urdf_path, 'r') as infp:
        robot_description_content = infp.read()

    # 1. Publică starea robotului bazată pe slider-ele de joint-uri
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content, 'use_sim_time': False}]
    )

    # 2. Lansează fereastra cu slidere pentru a roti manual fiecare joint
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen'
    )

    # 3. Pornește RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
    )

    return LaunchDescription([
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node
    ])
