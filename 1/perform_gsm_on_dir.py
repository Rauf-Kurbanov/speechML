from __future__ import division

import argparse
import errno
import numpy as np
import os
import subprocess
import shutil
import textwrap


def perform_gsm_on_folder(input_folder, output_folder, norm=False):
    """
    Performs emulation of bad phone line conditions on a set of audio files. Creates a replica of
    the data folder.
    """
    # check the are no trailing slashes
    if input_folder[-1] == '/':
        input_folder = input_folder[0:-1]
    if output_folder[-1] == '/':
        output_folder = output_folder[0:-1]

    # Make sure sox is installed
    try:
        subprocess.Popen(['sox', '--help'], stdout=open(os.devnull, 'wb'))
    except OSError:
        raise OSError("Worsening of audio with GSM codec requires sox to be installed.")

    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    # Get all files from folder
    file_list_input = []
    file_list_output = []
    for dirpath, d, f in os.walk(input_folder):
        for file in f:
            if file[-4:] == '.wav' or file[-5:] == '.flac':
                file_list_input.append(os.path.join(dirpath, file))
                out_dir_path = os.path.join(dirpath, file).replace(input_folder, output_folder)
                if out_dir_path[-5:] == '.flac':
                    out_dir_path = out_dir_path[:-4] + 'wav'
                file_list_output.append(out_dir_path)
            else:
                # copy the rest of the files in the similar directories
                nonaudiofile_input = os.path.join(dirpath, file)
                nonaudiofile_output = os.path.join(dirpath, file).replace(input_folder, output_folder)
                nonaudiofile_output_folder = os.path.split(nonaudiofile_output)[0]
                if not os.path.isdir(nonaudiofile_output_folder):
                    mkdir_p(nonaudiofile_output_folder)
                shutil.copyfile(nonaudiofile_input, nonaudiofile_output)

    file_list_input = np.array(file_list_input)
    file_list_output = np.array(file_list_output)

    print(file_list_input)

    for file_id in range(len(file_list_input)):
        input_file = file_list_input[file_id]
        output_file = file_list_output[file_id]
        print('Processing file ' + input_file + ' (#'
              + str(file_id) + '/' + str(len(file_list_input))
              + ', ' + str(file_id*100/len(file_list_input)) + '%)')

        # make sure the folder for the output file exists
        output_file_folder = os.path.split(output_file)[0]
        if not os.path.isdir(output_file_folder):
            mkdir_p(output_file_folder)

        sox_norm = '--norm ' if norm else ''
        # encode
        gsm_file = output_file + '.gsm'
        os.system('sox ' + sox_norm + input_file +
                  ' -r 8000 -c 1 ' + gsm_file + ' lowpass 4000 ' +
                  'compand 0.02,0.05 -60,-60,-30,-10,-20,-8,-5,-8,-2,0 -10 -7 0.05')
        # decode
        os.system('sox ' + gsm_file + ' -V -r 8000 -e signed-integer ' + output_file)

        # delete the temp
        os.system('rm ' + gsm_file)


def mkdir_p(path):
    """
    Recursive mkdir. http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prefix_chars='-+',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
            GSM emulator
            Software for performing simulation of gsm codec distortions on audio corpus
        '''))

    parser.add_argument('-in_corpus_path', help='Path to the original audio corpus to corrupt ',
                        required=True,
                        dest='in_corpus_path')
    parser.add_argument('-out_corpus_path', help='Output path to the corrupted corpus ',
                        required=True,
                        dest='out_corpus_path')
    parser.add_argument('-norm', help='Normalize level', default= False, required=False, dest='norm')
    args = parser.parse_args()
    perform_gsm_on_folder(args.in_corpus_path, args.out_corpus_path, norm=args.norm)
