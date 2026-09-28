#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
import math

# --- Offset-urile senzorilor fata de robot (din URDF, joint-uri fixe) ---
# Ajusteaza aici daca schimbi pozitia senzorilor in URDF.
SENSOR_OFFSETS = {
    'front_left':   (-0.06, 0.04),
    'front_center': ( 0.00, 0.04),
    'front_right':  ( 0.06, 0.04),
}

# --- Geometria liniilor negre (din world SDF l_open_track_world2.sdf) ---
# fiecare linie: (x_min, x_max, y_min, y_max) in coordonate world.
# Daca modifici traseul in .sdf, actualizeaza si aici.
LINE_SEGMENTS = [
    (-0.04, 0.04, 0.0, 3.0),    # line_vertical: pose 0 1.5, size 0.08 x 3.0
    (0.0, 3.0, 2.96, 3.04),     # line_horizontal: pose 1.5 3.0, size 3.0 x 0.08
    (-0.04, 0.04, 2.96, 3.04),  # line_corner: pose 0 3.0, size 0.08 x 0.08
]

# Toleranta suplimentara (marja in metri), ca sa compensam mici erori de odometrie
MARGIN = 0.01


class LineSensorGroundTruth(Node):
    def __init__(self):
        super().__init__('line_sensor_ground_truth')

        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.odom_received = False

        self.create_subscription(Odometry, '/odom', self._on_odom, 10)

        self.pubs = {}
        for name in SENSOR_OFFSETS:
            self.pubs[name] = self.create_publisher(Bool, f'line_sensor/{name}', 10)

        # bucla la 50Hz, calculeaza si publica pe baza ultimei pozitii cunoscute
        self.timer = self.create_timer(0.02, self._control_loop)

        self.get_logger().info(
            'Line Sensor Ground Truth pornit (fara randare, bazat pe /odom).'
        )

    def _on_odom(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        # yaw din quaternion
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.robot_yaw = math.atan2(siny_cosp, cosy_cosp)

        self.odom_received = True

    def _is_on_line(self, x: float, y: float) -> bool:
        for x_min, x_max, y_min, y_max in LINE_SEGMENTS:
            if (x_min - MARGIN) <= x <= (x_max + MARGIN) and (y_min - MARGIN) <= y <= (y_max + MARGIN):
                return True
        return False

    def _control_loop(self):
        if not self.odom_received:
            return

        cos_yaw = math.cos(self.robot_yaw)
        sin_yaw = math.sin(self.robot_yaw)

        for name, (offset_x, offset_y) in SENSOR_OFFSETS.items():
            # roteste offset-ul local cu orientarea robotului, apoi adauga pozitia robotului
            world_x = self.robot_x + (offset_x * cos_yaw - offset_y * sin_yaw)
            world_y = self.robot_y + (offset_x * sin_yaw + offset_y * cos_yaw)

            msg = Bool()
            msg.data = self._is_on_line(world_x, world_y)
            self.pubs[name].publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LineSensorGroundTruth()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()