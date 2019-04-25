import time
import pyaudio
import wave
from aip import AipSpeech
import random
import string
from pydub.audio_segment import AudioSegment
import os


# Settings
APP_ID = "16070198"
API_KEY = "rNFMfKG2duelK45ZuZgbTTXU"
SECRET_KEY = "gLXVE7fpuYHPaBtPxl1yRLt3e5p4KC8T"

RATE = "16000"
FORMAT = "wav"

framerate=16000
NUM_SAMPLES=2000
channels=1
sampwidth=2
TIME=2

# BaiduYuYin Client
client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)


def log(text):
    print("MySiri app log:", time.asctime(time.localtime(time.time())), " log: ", text)


def play_sound(filename):
    CHUNK = 1024
    wf = wave.open(filename, 'rb')

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)

    while data != b'':
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()

    p.terminate()


def save_wav_from_buffer(filename, buffer):
    if not os.path.exists("database"):
        os.mkdir("database")
    base_dir = "database/"
    framerate = 16000
    f = wave.open(base_dir + filename, "wb")
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(framerate)
    # 将wav_data转换为二进制数据写入文件
    f.writeframes(b"".join(buffer))
    f.close()


def save_synthesis(filename, result):
    if not isinstance(result, dict):
        base_path = "temp/"
        with open(base_path + filename + '.mp3', 'wb') as f:
            f.write(result)
        sound = AudioSegment.from_mp3(base_path + filename + ".mp3")
        sound.export(base_path + filename + ".wav", format='wav')
        return True
    else:
        return False


# 激活码生成
def activation_code(count, length):
    base = string.ascii_uppercase + string.ascii_lowercase + string.digits    # 生成激活码可能包含的字符集（大写字母、小写字母、数字）
    return [''.join(random.sample(base, length)) for i in range(count)]