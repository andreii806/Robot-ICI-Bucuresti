import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist
from enum import Enum, auto


class RobotState(Enum):
    LINE_FOLLOWING = auto()
    OBSTACLE_AVOIDANCE = auto()


class StateMachineNode(Node):

    def __init__(self):
        super().__init__('state_machine_node')

        self.state = RobotState.LINE_FOLLOWING
        self.state_start_time = self.get_clock().now()

        self.line_left = False
        self.line_center = False
        self.line_right = False

        self.dist_front = float('inf')
        self.dist_left = float('inf')
        self.dist_right = float('inf')

        self.obstacle_threshold = 0.20
        self.avoid_duration = 0.6
        self.linear_speed = 0.15
        self.angular_speed = 0.6

        self.create_subscription(Bool, '/line_follower/left', self.on_line_left, 10)
        self.create_subscription(Bool, '/line_follower/center', self.on_line_center, 10)
        self.create_subscription(Bool, '/line_follower/right', self.on_line_right, 10)

        self.create_subscription(Range, '/obstacle/front', self.on_dist_front, 10)
        self.create_subscription(Range, '/obstacle/left', self.on_dist_left, 10)
        self.create_subscription(Range, '/obstacle/right', self.on_dist_right, 10)

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.timer = self.create_timer(0.05, self.update)

    def on_line_left(self, msg):
        self.line_left = msg.data

    def on_line_center(self, msg):
        self.line_center = msg.data

    def on_line_right(self, msg):
        self.line_right = msg.data

    def on_dist_front(self, msg):
        self.dist_front = msg.range

    def on_dist_left(self, msg):
        self.dist_left = msg.range

    def on_dist_right(self, msg):
        self.dist_right = msg.range

    def update(self):
        elapsed = (self.get_clock().now() - self.state_start_time).nanoseconds / 1e9

        if self.state == RobotState.LINE_FOLLOWING:
            if self.dist_front < self.obstacle_threshold:
                self.state = RobotState.OBSTACLE_AVOIDANCE
                self.state_start_time = self.get_clock().now()
            else:
                self.publish_line_following()
        else:
            self.publish_avoidance()
            if elapsed >= self.avoid_duration:
                self.state = RobotState.LINE_FOLLOWING
                self.state_start_time = self.get_clock().now()

    def publish_line_following(self):
        cmd = Twist()
        if self.line_center:
            cmd.linear.x = self.linear_speed
        elif self.line_left:
            cmd.angular.z = self.angular_speed
        elif self.line_right:
            cmd.angular.z = -self.angular_speed
        self.cmd_pub.publish(cmd)

    def publish_avoidance(self):
        cmd = Twist()
        cmd.linear.x = -self.linear_speed
        cmd.angular.z = self.angular_speed if self.dist_left > self.dist_right else -self.angular_speed
        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = StateMachineNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
