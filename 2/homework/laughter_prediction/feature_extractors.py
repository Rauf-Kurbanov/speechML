import os
import tempfile
import librosa
import numpy as np
import pandas as pd
import scipy.io.wavfile as wav


class FeatureExtractor:
    def __init__(self, frame_sec):
        self.frame_sec = frame_sec

    def extract_features(self, wav_path):
        """
        Extracts features for classification ny frames for .wav file

        :param wav_path: string, path to .wav file
        :return: pandas.DataFrame with features of shape (n_chunks, n_features)
        """

        y, sr = librosa.load(wav_path, dtype=float)

        # Let's make and display a mel-scaled power (energy-squared) spectrogram
        frame_size = int(sr * self.frame_sec)


        fbank = []
        mfcc = []

        for i in range(0, len(y) - frame_size, int(frame_size / 5)):
            # Convert to log scale (dB). We'll use the peak power (max) as reference.
            val_fbank = librosa.feature.melspectrogram(y=y[i: i + int(frame_size / 5)], sr=sr)
            fbank.append(np.mean(np.log(val_fbank), axis=1))
            # Next, we'll extract the top 13 Mel-frequency cepstral coefficients (MFCCs)
            val_mfcc = librosa.feature.mfcc(y=y[i: i + int(frame_size / 5)], sr=sr)
            mfcc.append(np.mean(val_mfcc, axis=1))
        fbank = np.vstack(fbank)
        mfcc = np.vstack(mfcc)

        columns = list(map(lambda num: 'filterbank_' + str(num), list(range(fbank.shape[1])))) + \
                  list(map(lambda num: 'mfcc_' + str(num), list(range(mfcc.shape[1]))))

        return pd.DataFrame(np.hstack([fbank, mfcc]), columns=columns)

class PyAAExtractor(FeatureExtractor):
    """Python Audio Analysis features extractor"""
    def __init__(self):
        self.extract_script = "./extract_pyAA_features.py"
        self.py_env_name = "ipykernel_py2"

    def extract_features(self, wav_path):
        with tempfile.NamedTemporaryFile() as tmp_file:
            feature_save_path = tmp_file.name
            cmd = "python \"{}\" --wav_path=\"{}\" " \
                  "--feature_save_path=\"{}\"".format(self.extract_script, wav_path, feature_save_path)
            os.system("source activate {}; {}".format(self.py_env_name, cmd))

            feature_df = pd.read_csv(feature_save_path)
        return feature_df
