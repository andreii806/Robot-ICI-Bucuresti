import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String

DISTANTA_SIGURANTA = 0.4


class ObstacleAvoidanceNode(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance_node')

        self.distanta_fata = float('inf')
        self.distanta_stanga = float('inf')
        self.distanta_dreapta = float('inf')

      
        self.create_subscription(LaserScan, '/range_front', self.callback_fata, 10)
        self.create_subscription(LaserScan, '/range_left', self.callback_stanga, 10)
        self.create_subscription(LaserScan, '/range_right', self.callback_dreapta, 10)

    
        self.obstacle_pub = self.create_publisher(Bool, '/obstacle/detected', 10)

       
        self.direction_pub = self.create_publisher(String, '/obstacle/direction', 10)

       
        self.create_timer(0.1, self.evalueaza_si_publica)  

        self.get_logger().info('Nodul de evitare obstacole a pornit! (3 senzori)')

    def callback_fata(self, msg):
      
        if msg.ranges:
            self.distanta_fata = msg.ranges[0]

    def callback_stanga(self, msg):
        if msg.ranges:
            self.distanta_stanga = msg.ranges[0]

    def callback_dreapta(self, msg):
        if msg.ranges:
            self.distanta_dreapta = msg.ranges[0]

    def evalueaza_si_publica(self):
        obstacol_fata = self.distanta_fata < DISTANTA_SIGURANTA
        obstacol_stanga = self.distanta_stanga < DISTANTA_SIGURANTA
        obstacol_dreapta = self.distanta_dreapta < DISTANTA_SIGURANTA

        exista_obstacol = obstacol_fata or obstacol_stanga or obstacol_dreapta

        
        obstacol_msg = Bool()
        obstacol_msg.data = exista_obstacol
        self.obstacle_pub.publish(obstacol_msg)

        if not exista_obstacol:
            return

        directie = 'necunoscuta'
        if obstacol_fata:
            directie = 'fata'
            self.get_logger().warn(
                f'Obstacol in FATA la {self.distanta_fata:.2f}m!'
            )
        elif obstacol_stanga:
            directie = 'stanga'
            self.get_logger().warn(
                f'Obstacol in STANGA la {self.distanta_stanga:.2f}m!'
            )
        elif obstacol_dreapta:
            directie = 'dreapta'
            self.get_logger().warn(
                f'Obstacol in DREAPTA la {self.distanta_dreapta:.2f}m!'
            )

        directie_msg = String()
        directie_msg.data = directie
        self.direction_pub.publish(directie_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidanceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
