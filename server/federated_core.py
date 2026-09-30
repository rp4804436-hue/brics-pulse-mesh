import numpy as np

class FederatedOrchestrator:
    """
    Aggregates edge parameter weights across PHCs or BRICS partner nations
    without inspecting or centralizing raw patient records.
    """
    def __init__(self, num_features=4):
        # Initial model weights: [footfall, past_7d_burn, seasonal_factor, epidemic_indicator]
        self.global_weights = np.array([[0.35], [0.45], [0.15], [0.05]])
        self.global_bias = 5.0

    def federated_averaging(self, client_updates, epsilon=1.0):
        """
        Aggregates edge updates using FedAvg with Laplacian Differential Privacy.
        epsilon: Differential Privacy budget (smaller = more privacy/noise).
        """
        if not client_updates:
            return self.global_weights, self.global_bias

        total_samples = sum(c['samples'] for c in client_updates)
        weighted_w = np.zeros_like(self.global_weights)
        weighted_b = 0.0

        for update in client_updates:
            fraction = update['samples'] / total_samples
            weighted_w += fraction * update['weights']
            weighted_b += fraction * update['bias']

        # Apply Differential Privacy perturbation
        scale = 1.0 / (epsilon * total_samples)
        dp_noise_w = np.random.laplace(0, scale, size=self.global_weights.shape)
        dp_noise_b = float(np.random.laplace(0, scale, size=1)[0])

        self.global_weights = weighted_w + dp_noise_w
        self.global_bias = weighted_b + dp_noise_b
        return self.global_weights, self.global_bias

def run_local_edge_training(X, y, initial_weights, initial_bias, epochs=3, lr=0.01):
    w = initial_weights.copy()
    b = initial_bias
    n = len(X)
    for _ in range(epochs):
        preds = np.dot(X, w) + b
        loss_grad_w = (2 / n) * np.dot(X.T, (preds - y))
        loss_grad_b = (2 / n) * np.sum(preds - y)
        w -= lr * loss_grad_w
        b -= lr * loss_grad_b
    return {'weights': w, 'bias': b, 'samples': n}