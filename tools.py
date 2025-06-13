# tools.py
from bruges.filters import ricker, convolve
import numpy as np
from wedge import spectrum_analysis, spectrum_trim_small_val, wavelet_trim_small_val, create_figure
import matplotlib.pyplot as plt

def make_ricker(args):
    f = args['frequency']
    dt = args.get('dt', 0.001)
    duration = args.get('duration', 0.256)
    w, t = ricker(duration=duration, dt=dt, f=f)
    return {'wavelet': w.tolist(), 'time': t.tolist()}

def plot_ricker(args):
    wavelet = np.array(args['wavelet'])
    t = np.array(args.get('time', np.arange(len(wavelet))))
    t, wavelet = wavelet_trim_small_val(t, wavelet)
    freq, amp_spec, pow_spec = spectrum_analysis(t, wavelet)
    freq, amp_spec, pow_spec = spectrum_trim_small_val(freq, amp_spec, pow_spec)
    
    fig, axes = create_figure()
    ax0, ax1, ax2 = axes
    lw = 1.5
    ax0.plot(t, wavelet, color = 'black', lw = lw, label = 'wavelet')
    ax0.legend()
    ax0.fill_between(t, wavelet, 0, where = wavelet > 0, facecolor = [0.8, 0.8, 1.0], interpolate = True)
    ax0.fill_between(t, wavelet, 0, where = wavelet < 0, facecolor = [1.0, 0.8, 0.8], interpolate = True)
    ax0.set_xlabel('Time (ms)')
    ax0.set_ylabel('Amplitude')
    ax0.set_title('Ricker Wavelet', fontsize = 18)
    ax0.tick_params(top = True, right = True, labelright = True)
    ax0.grid(linestyle = ':')

    ax1.plot(freq, amp_spec, color = 'green', lw = lw, label = 'Amplitude spectrum')
    ax1.legend()
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('Amplitude (linear)')
    ax1.tick_params(top = True, right = True, labelright = True)
    ax1.grid(linestyle = ':')
    
    ax2.plot(freq, pow_spec, color = 'blue', lw = lw, label = 'Power spectrum (normalized)')
    ax2.legend()
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Power (dB)')
    ax2.set_ylim((-65, 5))
    ax2.tick_params(top = True, right = True, labelright = True)
    ax2.grid(linestyle = ':')
    
    plt.tight_layout()
    return fig

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
