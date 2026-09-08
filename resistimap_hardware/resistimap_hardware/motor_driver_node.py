#!/usr/bin/env python3
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

SIMULATE = True
DRIVE_TIME_PER_CELL_SEC = 1.5


class MotorDriverNode(Node):
    def __init__(self):
        super().__init__('motor_driver_node')
        self.arrived_pub = self.create_publisher(String, 'motor/arrived', 10)
        self.goto_sub = self.create_subscription(String, 'motor/goto_cell', self.on_goto_cell, 10)
        self.get_logger().info('motor_driver_node started (SIMULATE mode).')

    def on_goto_cell(self, msg):
        cell = msg.data
        self.get_logger().info(f'Driving to cell {cell}...')
        time.sleep(DRIVE_TIME_PER_CELL_SEC)
        arrived_msg = String()
        arrived_msg.data = cell
        self.arrived_pub.publish(arrived_msg)
        self.get_logger().info(f'Arrived at cell {cell}.')


def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
