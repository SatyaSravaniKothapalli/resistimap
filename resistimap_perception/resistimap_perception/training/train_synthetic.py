#!/usr/bin/env python3
"""
train_synthetic.py
-------------------
THROWAWAY / PLACEHOLDER SCRIPT.

Trains the risk-classifier MLP on randomly generated resistivity values,
labeled using the real Langford & Broomfield thresholds. This exists ONLY
to prove the training -> save -> load -> predict pipeline works, before
real slab data is available.

The model this produces (model_synthetic.pt) must NEVER be used as the
final result. Once real slab readings are collected, re-run this same
architecture on real data using train_real.py (to be written later) and
that becomes the actual model used in risk_classifier_node.
"""

import random

import torch
import torch.nn as nn
import torch.optim as optim

# ---- Langford & Broomfield thresholds (Ohm-m) ----
LABELS = ["very_high", "high", "low_moderate", "low"]


def label_for_rho(rho):
    if rho < 50:
        return 0  # very_high
    elif rho < 100:
        return 1  # high
    elif rho < 200:
        return 2  # low_moderate
    else:
        return 3  # low


def generate_synthetic_dataset(n=2000):
    X = []
    y = []
    for _ in range(n):
        rho = random.uniform(1, 500)
        X.append([rho])
        y.append(label_for_rho(rho))
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.long)


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


def main():
    X, y = generate_synthetic_dataset(n=2000)

    model = RiskClassifierMLP()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    epochs = 200
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 50 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

    # Quick sanity check
    test_values = [30.0, 75.0, 150.0, 300.0]
    model.eval()
    with torch.no_grad():
        for v in test_values:
            pred = model(torch.tensor([[v]], dtype=torch.float32))
            label_idx = torch.argmax(pred, dim=1).item()
            print(f"rho={v} -> predicted={LABELS[label_idx]}")

    save_path = "model_synthetic.pt"
    torch.save(model.state_dict(), save_path)
    print(f"\nTHROWAWAY model saved to {save_path} (synthetic data only, do NOT use as final model)")


if __name__ == "__main__":
    main()
