#!/usr/bin/env python3
import os
import argparse

import numpy as np 
import librosa
import wavio

def process(args):
    file_list = [f for f in os.listdir(args.source_folder) if f.endswith('.wav')]
    troublesome = []
    for f in file_list:
        file_path = os.path.join(args.source_folder, f)
        data, sr = librosa.load(file_path, sr=args.resample)
        data = (data * np.iinfo(np.int16).max).astype(np.int16)
        file_duration = float(len(data)) / sr
        if file_duration < args.duration:
            troublesome.append((f, 'File too short'))
            continue

        window_length = int(args.window_length  * sr)
        final_length = int(sr * args.duration)
        try:
            res = trim(data, window_length, final_length)
        except:
            troublesome.append((f, "Unsure"))
        dest_file = os.path.join(args.destination_folder, f)
        wavio.write(dest_file, res, sr)
        with open(os.path.join(args.destination_folder, "troublesome.txt"), 'w') as f:
            f.writelines([' -> '.join(elem) + '\n' for elem in troublesome])

def trim(signal, window_length, final_length):
    length_sig = len(signal)    
    en = sig_energy(signal, window_length)
    sup_th = np.argwhere(en > np.mean(en))
    start_point = np.squeeze(sup_th[0]) * window_length
    stop_point = np.squeeze(sup_th[-1]) * window_length
    len_th = (stop_point - start_point)
    reliquat = final_length - len_th
    if reliquat < 0:
        raise Exception
    if start_point - (reliquat // 2) < 0:
        return signal[:final_length]
    if stop_point + (reliquat //2) > length_sig:
        return signal[-final_length:]
    return signal[start_point - (reliquat // 2):stop_point + (reliquat //2)]

def sig_energy(signal, window_length):
    def split(signal, window_length):
        frames = [np.array(signal[i * window_length : (i * window_length) + window_length]) for i in range(len(signal) // window_length)]
        return np.array(frames).astype(np.float32)
    
    def energy(frame):
        return np.sum(frame**2)

    return [energy(f) for f in split(signal, window_length)]

def main():
    parser = argparse.ArgumentParser(description='Trimmer is designed to process a batch a wav files by trimming them to a specified duration around a speech segment.')
    parser.add_argument('source_folder', help="Source folder containing wav files")
    parser.add_argument('destination_folder', help="Destintion folder where trimmed files will be written")
    parser.add_argument('duration', type=float, help='Desired duration in second')
    parser.add_argument('--window_length', dest='window_length', default=0.064, type=float, help='Analysis window length in second')
    parser.add_argument('--resample', dest="resample", default=None, type=int, help="Resample file to given sample rate prior to trimming")
    args = parser.parse_args()

    assert os.path.isdir(args.source_folder), "Could not find source folder"
    if not os.path.isdir(args.destination_folder):
        try:
            os.mkdir(args.destination_folder)
        except:
            print('Error: Could not create destination folder {}'.format(args.destination_folder))

    process(args)

if __name__ =="__main__":
    main()