#!/usr/bin/env python3
"""
Reusable eye diagram generator module that can be imported and used
automatically after simulations.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft

def generate_waveform(bit_sequence, samples_per_bit=16):
    """Generate digital waveform from bit sequence"""
    waveform = []
    
    for bit in bit_sequence:
        # Convert bit to level (-1 or +1)
        level = -1 if bit == 0 else 1
        
        # Add samples for this bit (rectangular pulse)
        waveform.extend([level] * samples_per_bit)
    
    return np.array(waveform)

def parse_complex_number(s):
    """Parse complex number from string like '9.999999999999998510e+07+0.000000000000000000e+00j'"""
    s = s.strip('()')
    
    # Find the position where the imaginary part starts
    # Look for '+' or '-' that's not part of scientific notation
    imag_start = -1
    for i, char in enumerate(s):
        if char in '+-' and i > 0 and s[i-1] not in 'eE':
            imag_start = i
            break
    
    if imag_start > 0:
        real_part = s[:imag_start]
        imag_part = s[imag_start:].replace('j', '').strip()
    else:
        # Simple real number
        return complex(float(s), 0)
    
    try:
        real = float(real_part)
        imag = float(imag_part)
        return complex(real, imag)
    except ValueError as e:
        print(f"Error parsing complex number: {s}")
        print(f"Real part: {real_part}, Imag part: {imag_part}")
        raise e

def generate_waveform_from_sparams(sparams_file, bit_sequence, samples_per_bit=16, sample_rate=1.07e9*16):
    """Generate waveform using S-parameters from file"""
    # Load S-parameters - they contain complex numbers in parentheses
    frequencies = []
    s21 = []
    
    with open(sparams_file, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 3:
                    freq_str = parts[0].strip('()')
                    s21_str = parts[2].strip('()')
                    frequencies.append(parse_complex_number(freq_str).real)  # Frequency is real part
                    s21.append(parse_complex_number(s21_str))
    
    frequencies = np.array(frequencies)
    s21 = np.array(s21)
    
    # Generate basic waveform first
    waveform_in = generate_waveform(bit_sequence, samples_per_bit)
    
    # Apply simple frequency-dependent filtering based on S21
    fft_in = fft(waveform_in)
    freq_bins = np.fft.fftfreq(len(waveform_in), d=1/sample_rate)
    
    # Create frequency response from S21 data (simple interpolation)
    freq_response = np.ones_like(freq_bins, dtype=complex)
    for i, freq in enumerate(freq_bins):
        if freq >= 0:  # Only positive frequencies
            freq_response[i] = np.interp(freq, frequencies, s21)
        else:
            # Mirror for negative frequencies
            freq_response[i] = np.conj(freq_response[len(freq_bins) - i - 1])
    
    # Apply frequency response
    fft_out = fft_in * freq_response

    # Calculate correlation to estimate time delay
    fft_corr = fft_out * np.conj(fft_in)
    corr = np.real(ifft(fft_corr))
    td = - np.argmax(np.abs(corr)) / sample_rate

    # Correct the time delay (zd for zero delay)
    fft_out_zd = fft_out * np.exp(-1j*2*np.pi*td*freq_bins)

    waveform_out = np.real(ifft(fft_out_zd))
    
    return waveform_in, waveform_out, freq_response

def generate_eye_diagrams(sparams_file, output_prefix, bit_rate=1.07e9, samples_per_bit=16, 
                         bit_sequence=None, verbose=True):
    """
    Generate comprehensive eye diagrams from S-parameters
    
    Args:
        sparams_file: Path to S-parameters CSV file
        output_prefix: Prefix for output image files (e.g., 'eye-diagram/sim-name')
        bit_rate: Bit rate in Hz
        samples_per_bit: Number of samples per bit
        bit_sequence: Optional custom bit sequence
        verbose: Whether to print progress information
    """
    if bit_sequence is None:
        # Default 128-bit pseudorandom sequence for reproducibility
        # From https://www.random.org/bytes/
        import re
        bit_string = """01110111 01001110 01110001 01101011 00111100 01010100 10001100 01100011 
            10010011 00111111 01001010 10110110 01110111 11010010 11111101 01001100"""
        bit_sequence = [int(bit) for bit in re.sub(r'\s+', '', bit_string)]
    
    sampling_rate = bit_rate * samples_per_bit
    
    if verbose:
        print(f"Generating eye diagrams from {sparams_file}")
        print(f"Configuration: {bit_rate/1e9:.1f} Gbps, {sampling_rate/1e9:.1f} GS/s, {samples_per_bit} samples/bit")
    
    # Generate waveforms using S-parameters
    original_waveform, filtered_waveform, freq_response = generate_waveform_from_sparams(
        sparams_file, bit_sequence, samples_per_bit, sampling_rate
    )
    
    # Time axis in nanoseconds
    time_ns = np.arange(len(original_waveform)) / sampling_rate * 1e9
    num_bits = len(original_waveform) // samples_per_bit
    
    if verbose:
        print(f"Waveform analysis:")
        print(f"  Original range: [{np.min(original_waveform):.3f}, {np.max(original_waveform):.3f}]")
        print(f"  Filtered range: [{np.min(filtered_waveform):.3f}, {np.max(filtered_waveform):.3f}]")
    
    # Plot 1: Time domain comparison
    plt.figure(figsize=(12, 6))
    plt.plot(time_ns, original_waveform, 'b-', linewidth=2, alpha=0.7, label='Original')
    plt.plot(time_ns, filtered_waveform, 'r-', linewidth=2, label='S-Parameter Filtered')
    plt.xlabel('Time (ns)')
    plt.ylabel('Amplitude')
    plt.title('Time Domain: Original vs S-Parameter Filtered')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'{output_prefix}-time-domain.png', dpi=300)
    plt.close()
    
    # Plot 2: Combined Frequency analysis with dual y-axis
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # Compute FFT of original and filtered waveforms
    fft_original = np.fft.fft(original_waveform)
    fft_filtered = np.fft.fft(filtered_waveform)
    freq_bins = np.fft.fftfreq(len(original_waveform), d=1/sampling_rate)
    pos_freq_mask = freq_bins >= 0
    
    # Plot original and filtered waveform spectra on primary y-axis (left)
    ax1.plot(freq_bins[pos_freq_mask] / 1e9, np.abs(fft_original[pos_freq_mask]), 'b-', linewidth=2, alpha=0.7, label='Original Spectrum')
    ax1.plot(freq_bins[pos_freq_mask] / 1e9, np.abs(fft_filtered[pos_freq_mask]), 'r-', linewidth=2, alpha=0.7, label='Filtered Spectrum')
    ax1.set_xlabel('Frequency (GHz)')
    ax1.set_ylabel('Spectrum Magnitude', color='k')
    ax1.tick_params(axis='y', labelcolor='k')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, sampling_rate/(2*1e9))  # Up to Nyquist
    
    # Create secondary y-axis for S-parameters
    ax2 = ax1.twinx()
    ax2.plot(freq_bins[pos_freq_mask] / 1e9, np.abs(freq_response[pos_freq_mask]), 'g-', linewidth=2, label='S21 Magnitude')
    ax2.set_ylabel('S21 Magnitude', color='g')
    ax2.tick_params(axis='y', labelcolor='g')
    
    plt.title('Frequency Analysis: Spectra with S21 Response (Secondary Axis)')
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}-freq.png', dpi=300)
    plt.close()
    
    # Plot 3: Combined Eye diagram - Original (blue) and Filtered (red) on same plot
    plt.figure(figsize=(12, 6))
    for i in range(1, num_bits):
        start_idx = i * samples_per_bit
        end_idx = start_idx + samples_per_bit
        
        # Original waveform in blue
        bit_slice_orig = original_waveform[start_idx:end_idx]
        time_slice = time_ns[start_idx:end_idx] - time_ns[start_idx]
        plt.plot(time_slice, bit_slice_orig, 'b-', linewidth=1, alpha=0.3)
        
        # Filtered waveform in red
        bit_slice_filt = filtered_waveform[start_idx:end_idx]
        plt.plot(time_slice, bit_slice_filt, 'r-', linewidth=1, alpha=0.3)
    
    plt.xlabel('Time within bit period (ns)')
    plt.ylabel('Amplitude')
    plt.title('Eye Diagram: Original (Blue) vs S-Parameter Filtered (Red)')
    plt.grid(True, alpha=0.3)
    plt.legend(['Original', 'S-Parameter Filtered'])
    plt.tight_layout()
    plt.savefig(f'{output_prefix}-eye.png', dpi=300)
    plt.close()
    
    if verbose:
        print(f"Eye diagrams generated:")
        print(f"  - {output_prefix}-time-domain.png")
        print(f"  - {output_prefix}-freq.png")
        print(f"  - {output_prefix}-eye.png")
    
    return {
        'original_waveform': original_waveform,
        'filtered_waveform': filtered_waveform,
        'freq_response': freq_response,
        'time_ns': time_ns
    }

if __name__ == "__main__":
    # Example usage
    generate_eye_diagrams(
        'sim/sim-single-slot-S.csv',
        'eye-diagram/test-output'
    )
