# tools.py
from bruges.filters import ricker, convolve
import numpy as np

def make_ricker(args):
    f = args['frequency']
    dt = args.get('dt', 0.001)
    duration = args.get('duration', 0.256)
    w, t = ricker(duration=duration, dt=dt, f=f)
    return {'wavelet': w.tolist(), 'time': t.tolist()}

def compute_reflectivity(args):
    vp = np.array(args['vp'])
    rho = np.array(args.get('rho', [2200]*len(vp)))
    Z = vp * rho
    rc = (Z[1:] - Z[:-1]) / (Z[1:] + Z[:-1])
    reflectivity = np.zeros(args.get('n_samples', 1000))
    positions = args.get('positions', [100, 300])  # indices
    for i, pos in enumerate(positions):
        reflectivity[pos] = rc[i]
    return {'reflectivity': reflectivity.tolist()}
