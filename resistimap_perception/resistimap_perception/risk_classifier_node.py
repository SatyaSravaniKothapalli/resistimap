#!/usr/bin/env python3
"""
risk_classifier_node
---------------------
Subscribes to Resistivity messages, runs the trained MLP (currently the
THROWAWAY synthetic model), and publishes a RiskClassification message.
"""

import os

import torch
import torch.nn as nn

import rclpy
from rclpy.node import Node

from resistimap_msgs.msg import Resistivity, RiskClassification

LABELS = ["very_high", "high", "low_moderate", "low"]

# Path to the trained model. Currently points at the throwaway synthetic
# model. Update this once a real model (trained on actual slab data) exists.
MODEL_PATH = os.path.expanduser(
    "~/resistimap_ws/src/resistimap_perception/resistimap_perception/training/model_synthetic.pt"
)


class RiskClassifierMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
        )

    def forward(self, x):
        return self.net(x)


class RiskClassifierNode(Node):
    def __init__(self):
        super().__init__('risk_classifier_node')

        self.model = RiskClassifierMLP()
        self.model.load_state_dict(torch.load(MODEL_PATH, map_location='cpu'))
        self.model.eval()
        self.get_logger().info(f'Loaded model from {MODEL_PATH} (SYNTHETIC/PLACEHOLDER model).')

        self.publisher_ = self.create_publisher(RiskClassification, 'risk_classification', 10)
        self.subscription = self.create_subscription(
            Resistivity, 'resistivity', self.on_resistivity, 10
        )

    def on_resistivity(self, msg):
        with torch.no_grad():
            x = torch.tensor([[msg.rho]], dtype=torch.float32)
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)
            label_idx = torch.argmax(probs, dim=1).item()
            confidence = probs[0][label_idx].item()

        out = RiskClassification()
        out.header = msg.header
        out.grid_x = msg.grid_x
        out.grid_y = msg.grid_y
        out.rho = msg.rho
        out.label = LABELS[label_idx]
        out.confidence = confidence

        self.publisher_.publish(out)
        self.get_logger().info(
            f'rho={msg.rho:.2f} -> label={out.label} (confidence={confidence:.2f})'
        )


def main(args=None):
    rclpy.init(args=args)
    node = RiskClassifierNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
