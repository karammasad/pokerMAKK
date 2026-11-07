"""Fit a compact two-hidden-layer MLP using NumPy and save pure-NumPy weights."""
import argparse
from pathlib import Path
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).with_name("train_data.npz")))
    ap.add_argument("--out", default=str(Path(__file__).parents[1] / "weights" / "equity.npz"))
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=512)
    args = ap.parse_args()
    d = np.load(args.data)
    x, y = d["x"], d["y"].reshape(-1, 1)
    rng = np.random.default_rng(17)
    split = int(0.8 * len(x))
    order = rng.permutation(len(x))
    train_ix, test_ix = order[:split], order[split:]
    mean, std = x[train_ix].mean(axis=0, keepdims=True), x[train_ix].std(axis=0, keepdims=True)
    x = (x - mean) / np.maximum(std, 1e-5)
    x_train, y_train = x[train_ix], y[train_ix]
    x_test, y_test = x[test_ix], y[test_ix]
    w1 = rng.normal(0, 0.2, (x.shape[1], 64)).astype(np.float32); b1 = np.zeros((1, 64), np.float32)
    w2 = rng.normal(0, 0.15, (64, 32)).astype(np.float32); b2 = np.zeros((1, 32), np.float32)
    w3 = rng.normal(0, 0.1, (32, 1)).astype(np.float32); b3 = np.zeros((1, 1), np.float32)
    # Full-batch gradient descent with a shuffled minibatch stream.
    params = [w1, b1, w2, b2, w3, b3]
    m = [np.zeros_like(p) for p in params]; v = [np.zeros_like(p) for p in params]
    step, lr = 0, 0.003
    for epoch in range(args.epochs):
        order = rng.permutation(len(x_train))
        loss_sum = 0.0
        for start in range(0, len(order), args.batch):
            ix = order[start:start + args.batch]
            xb, yb = x_train[ix], y_train[ix]
            z1 = xb @ w1 + b1; h1 = np.tanh(z1)
            z2 = h1 @ w2 + b2; h2 = np.tanh(z2)
            pred = h2 @ w3 + b3
            err = (pred - yb) * (2.0 / len(ix)); loss_sum += float(np.mean((pred-yb)**2))
            g3 = h2.T @ err; gb3 = err.sum(axis=0, keepdims=True)
            dh2 = err @ w3.T * (1 - h2*h2)
            g2 = h1.T @ dh2; gb2 = dh2.sum(axis=0, keepdims=True)
            dh1 = dh2 @ w2.T * (1 - h1*h1)
            g1 = xb.T @ dh1; gb1 = dh1.sum(axis=0, keepdims=True)
            step += 1
            for j, (p, g) in enumerate(zip(params, [g1, gb1, g2, gb2, g3, gb3])):
                m[j] = 0.9*m[j] + 0.1*g; v[j] = 0.999*v[j] + 0.001*g*g
                p -= lr * (m[j]/(1-0.9**step)) / (np.sqrt(v[j]/(1-0.999**step)) + 1e-8)
        print(f"epoch={epoch+1} train_mse={loss_sum/max(1,(len(x_train)+args.batch-1)//args.batch):.5f}")
    z1 = np.tanh(x_test @ w1 + b1)
    z2 = np.tanh(z1 @ w2 + b2)
    test_pred = np.clip(z2 @ w3 + b3, 0.02, 0.98)
    print(f"heldout_mae={np.mean(np.abs(test_pred-y_test)):.5f} heldout_rmse={np.sqrt(np.mean((test_pred-y_test)**2)):.5f}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, w1=w1,b1=b1,w2=w2,b2=b2,w3=w3,b3=b3,mean=mean,std=std,
                        test_mae=np.float32(np.mean(np.abs(test_pred-y_test))))

if __name__ == "__main__":
    main()
