#!/usr/bin/env python3
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool

SIMULATE = True
ACTUATE_TIME_SEC = 0.5


class ProbeActuatorNode(Node):
    def __init__(self):
        super().__init__('probe_actuator_node')
        self.done_pub = self.create_publisher(Bool, 'probe/lowered', 10)
        self.lower_sub = self.create_subscription(String, 'probe/command', self.on_command, 10)
        self.get_logger().info('probe_actuator_node started (SIMULATE mode).')

    def on_command(self, msg):
        command = msg.data
        if command == 'lower':
            self.get_logger().info('Lowering probes...')
            time.sleep(ACTUATE_TIME_SEC)
            self.done_pub.publish(Bool(data=True))
            self.get_logger().info('Probes lowered.')
        elif command == 'raise':
            self.get_logger().info('Raising probes...')
            time.sleep(ACTUATE_TIME_SEC)
            self.done_pub.publish(Bool(data=False))
            self.get_logger().info('Probes raised.')
        else:
            self.get_logger().warn(f'Unknown probe command: {command}')


def main(args=None):
    rclpy.init(args=args)
    node = ProbeActuatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
