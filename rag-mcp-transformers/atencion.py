"""Parte 4: una capa de atención de transformer, solo con NumPy."""
import numpy as np


def softmax(M):
    """Softmax por fila (último eje). Resta el máximo para no desbordar exp."""
    e = np.exp(M - M.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)


def atencion(Q, K, V, mascara=False):
    """A = softmax(Q K^T / sqrt(d_k)); devuelve (A @ V, A)."""
    puntajes = Q @ K.T / np.sqrt(Q.shape[-1])
    if mascara:  # causal: el token i no ve a los j > i
        n = puntajes.shape[0]
        puntajes = np.where(np.triu(np.ones((n, n), bool), 1), -np.inf, puntajes)
    A = softmax(puntajes)
    return A @ V, A


def autoatencion(X, Wq, Wk, Wv, mascara=False):
    """Q, K y V salen del mismo X."""
    return atencion(X @ Wq, X @ Wk, X @ Wv, mascara)


def multicabeza(X, cabezas, Wo, mascara=False):
    """Una autoatención por cabeza, concatenadas por columnas y proyectadas con Wo."""
    return np.concatenate([autoatencion(X, *c, mascara)[0] for c in cabezas], axis=1) @ Wo


def layer_norm(x, eps=1e-5):
    """Normaliza cada fila a media 0 y varianza 1 (sin gamma ni beta)."""
    return (x - x.mean(-1, keepdims=True)) / np.sqrt(x.var(-1, keepdims=True) + eps)
