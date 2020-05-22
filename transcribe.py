import os
import argparse


def cut_audio(path_audio, start=None, end=None, output_format='mp3', path_output=None):
    import pydub
    import re
    info = pydub.utils.mediainfo(path_audio)
    print('Loading adudio file {}'.format(path_audio))
    sound = pydub.AudioSegment.from_file(path_audio)
    duration = float(info['duration'])
    cut_sound = sound[int(start/duration * len(sound)): int(end/duration * len(sound))] if start is not None and end is not None else sound
    path_cut = re.sub('\..*$', '-cut-{}_{}.{}'.format(start, end, output_format), path_audio)
    if path_output:
        cut_sound.export(path_output, format=output_format) #Exports to a wav file in the current path.
    else:
        cut_sound.export(path_cut, format=output_format) #Exports to a wav file in the current path.
    print(
        'File {} cut to {}'.format(
            path_audio, path_output if path_output else path_cut
        )
    )
    file_name = path_output.split('/')[-1] if path_output else path_cut.split('/')[-1]
    return path_cut, file_name


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    from google.cloud import storage
    '''Uploads a file to the bucket.'''
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    storage_uri = os.path.join('gs://', bucket_name, destination_blob_name)
    print(
        'File {} uploaded to {}'.format(
            source_file_name, storage_uri
        )
    )
    return storage_uri

def sample_long_running_recognize(storage_uri, language_code='zh-CN', path_vocab='', sample_rate_hertz=16000):
    from google.cloud import speech_v1
    from google.cloud.speech_v1p1beta1 import enums
    from google.cloud import speech
    client = speech_v1.SpeechClient()
    encoding = enums.RecognitionConfig.AudioEncoding.MP3 if storage_uri.endswith('.mp3') else enums.RecognitionConfig.AudioEncoding.LINEAR16
    recording_device_type = enums.RecognitionMetadata.RecordingDeviceType.PC
    interaction_type = enums.RecognitionMetadata.InteractionType.PRESENTATION
    speech_context = None
    if path_vocab:
        with open(path_vocab, 'r') as f:
            phrases = f.read().split('\n')
        speech_context = speech.types.SpeechContext(phrases=phrases)
    metadata = {
        'interaction_type': interaction_type,
        'recording_device_type': recording_device_type,
    }
    config = {
        'metadata': metadata,
        'language_code': language_code,
        'sample_rate_hertz': sample_rate_hertz,
        'encoding': encoding,
        'enable_automatic_punctuation': True,
        'audio_channel_count': 2,
        'enable_word_time_offsets':True,
    }
    if speech_context:
        config.update({
            'speech_contexts': [speech_context]
        })
    audio = {'uri': storage_uri}
    operation = client.long_running_recognize(config, audio)
    print('Waiting for operation to complete on file {}...'.format(storage_uri))
    response = operation.result()
    for result in response.results:
        # First alternative is the most probable result
        alternative = result.alternatives[0]
    return response

def write_transcript(response, path_transcript, start_seconds=0):
    transcript = ''
    for result in response.results:
        alternative = result.alternatives[0]
        total_seconds = None
        words = alternative.words
        if any(words):
            start_time = getattr(words[0], 'start_time')
            if start_time:
                total_seconds = start_time.seconds + start_seconds
        h = 0
        if total_seconds:
            m, s = divmod(int(total_seconds), 60)
            h, m = divmod(m, 60)
        t = alternative.transcript.encode('utf8')
        transcript = transcript + "{:0>2d}:{:0>2d}:{:0>2d} {}\n".format(h, m, s, t)
    with open(path_transcript, 'w') as f:
        f.write(transcript)
    return transcript

def create_parser():
    parser = argparse.ArgumentParser()
    # Required parameters
    parser.add_argument(
        '--path_audio',
        default='/Users/straynwang/Downloads/tantian.m4a',
        type=str,
        help='The input audio file path.',
    )
    parser.add_argument(
        '--path_vocab',
        default='/tmp/speech-to-text/vocab.txt',
        type=str,
        help='The input audio file path.',
    )
    parser.add_argument(
        '--language_code',
        default='zh-CN',
        type=str,
        help='Default language for GCP speech2text',
    )
    parser.add_argument(
        '--start_min',
        default=None,
        type=float,
        help='Starting minute of the audio',
    )
    parser.add_argument(
        '--end_min',
        default=None,
        type=float,
        help='Ending minute of the audio',
    )
    return parser

if __name__ == '__main__':
    args = create_parser().parse_args()
    start, end = args.start_min * 60, args.end_min * 60
    BUCKET_NAME = '706-bucket'
    PATH_WORK = '/tmp/speech-to-text/'
    path_audio_cut, audio_file_name = cut_audio(args.path_audio, start, end)
    storage_uri = upload_blob(bucket_name=BUCKET_NAME, source_file_name=path_audio_cut, destination_blob_name=os.path.join('audio', audio_file_name))
    # transcibing remote audio
    response = sample_long_running_recognize(storage_uri, args.language_code, args.path_vocab)
    # write transcript to local
    os.system('mkdir -p {}'.format(PATH_WORK))
    path_transcript = os.path.join(PATH_WORK, 'transcript-{}-{}_{}.txt'.format(audio_file_name.replace('.mp3', ''), start, end))
    transcript = write_transcript(response, path_transcript, start_seconds=start)
    # upload transcript to remote
    storage_uri = upload_blob(bucket_name=BUCKET_NAME, source_file_name=path_transcript, destination_blob_name=os.path.join('text', path_transcript.split('/')[-1]))
    print(transcript)