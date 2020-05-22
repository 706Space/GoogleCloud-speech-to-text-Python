export PATH_AUDIO=$HOME/Documents/audio.mp3
export PATH_VOCAB=$HOME/speech-to-text/vocab.txt

echo "Running test step ..."
python $HOME/speech-to-text/transcribe.py --path_audio $PATH_AUDIO --path_vocab $PATH_VOCAB --start_min 8.3 --end_min 15

echo "Running actual transcription"
python $HOME/speech-to-text/transcribe.py --path_audio $PATH_AUDIO --path_vocab $PATH_VOCAB --start_min 10 --end_min 40
python $HOME/speech-to-text/transcribe.py --path_audio $PATH_AUDIO --path_vocab $PATH_VOCAB --start_min 40 --end_min 70
python $HOME/speech-to-text/transcribe.py --path_audio $PATH_AUDIO --path_vocab $PATH_VOCAB --start_min 70 --end_min 100

python $HOME/speech-to-text/transcribe.py --path_audio $PATH_AUDIO --path_vocab $PATH_VOCAB --start_min 100 --end_min 130
python $HOME/speech-to-text/transcribe.py --path_audio $PATH_AUDIO --path_vocab $PATH_VOCAB --start_min 130 --end_min 160
python $HOME/speech-to-text/transcribe.py --path_audio $PATH_AUDIO --path_vocab $PATH_VOCAB --start_min 160 --end_min 190