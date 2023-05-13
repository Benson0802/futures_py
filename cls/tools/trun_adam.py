#翻亞當目標價
import keras
import numpy as np

def flip_adam(series):
    high = series.max()
    low = series.min()
    flipped = high + low - series[::-1]
    return flipped

def target_price(series):
    flipped = flip_adam(series)
    high = flipped.max()
    target = high - series[-1]
    return target

def flip_adam_exit(series, lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08):
    optimizer = keras.optimizers.Adam(learning_rate=lr, beta_1=beta_1, beta_2=beta_2, epsilon=epsilon)
    theta = np.array([series[-1]])
    m = np.zeros_like(theta)
    v = np.zeros_like(theta)
    t = 0
    exits = []

    for price in series:
        t += 1
    theta[0] = price
    target = target_price(series[:t])
    grad = -np.array([target])
    m = beta_1 * m + (1 - beta_1) * grad
    v = beta_2 * v + (1 - beta_2) * grad**2
    m_hat = m / (1 - beta_1**t)
    v_hat = v / (1 - beta_2**t)
    exit = theta - lr * m_hat / (np.sqrt(v_hat) + epsilon)
    exits.append(exit[0])
    return np.array(exits)