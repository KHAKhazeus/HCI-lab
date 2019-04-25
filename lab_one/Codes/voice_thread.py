from PyQt5.QtCore import QThread, pyqtSignal
import speech_recognition
import pyaudio
from utils import *
import os

MY_NAME = "大白"


class VoiceThread(QThread):
    quit_signal = pyqtSignal()
    color_signal = pyqtSignal(tuple)
    mode_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.recognizer = speech_recognition.Recognizer()
        self.no_audio_times = 0
        self.mode = "zh"

    def run(self) -> None:
        while True:
            self.basic_loop()
            # 等待唤醒
            while True:
                code = self.record_once(True)
                with open(code, 'rb') as fp:
                    data = fp.read()
                    result = client.asr(data, 'wav', 16000, {
                        'dev_pid': 1536,
                    })
                    if result["err_no"] == 0 and result["err_msg"] == "success.":
                        line = " ".join(result["result"])
                        if line.find(MY_NAME) != -1:
                            play_sound("temp/wake_up.wav")
                            break

    def basic_loop(self):
        condition = True
        while condition:
            code = self.record_once(False)
            self.color_signal.emit((0, 0, 0))
            condition = self.recognize_once(code)
            self.sleep(1)


    def record_once(self, silence):
        if not silence:
            play_sound("temp/begin_listening.wav")
            self.color_signal.emit((64, 0, 60))
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pyaudio.paInt16, channels=1,
                         rate=framerate, input=True,
                         frames_per_buffer=NUM_SAMPLES)
        my_buf = []
        count = 0
        log("Speech Input")
        while count < TIME * 15:  # 控制录音时间
            string_audio_data = stream.read(NUM_SAMPLES)
            my_buf.append(string_audio_data)
            count += 1
        code = activation_code(1, 16)
        filename = str(code[0]) + ".wav"
        save_wav_from_buffer(filename, my_buf)
        stream.close()
        return "database/" + filename


    def process_once(self, command):
        if command.find("英文模式") != -1:
            play_sound("temp/chinese_to_english.wav")
            self.mode = "en"
            self.mode_signal.emit()
            return True
        elif command.lower().find("chinese mode") != -1:
            play_sound("temp/english_to_chinese.wav")
            self.mode = "zh"
            self.mode_signal.emit()
            return True
        elif command.lower().find("siri") != -1:
            play_sound("temp/open_siri.wav")
            os.system("open /Applications/Siri.app")
            return False
        elif command.lower().find("网易云音乐") != -1 or command.lower().find("音乐") != -1 or \
                command.lower().find("music") != -1:
            play_sound("temp/play_music.wav")
            os.system("open /Applications/NeteaseMusic.app")
            return False
        elif (command.lower().find("再") != -1 and command.lower().find("见") != -1) or \
                command.lower().find("退出") != -1 or \
                (command.lower().find("关闭") != -1 and command.lower().find("大白") != -1) \
                or command.lower().find("拜拜") != -1:
            play_sound("temp/quit.wav")
            self.quit_signal.emit()
        else:
            return True

    def recognize_once(self, filePath):
        with open(filePath, 'rb') as fp:
            data = fp.read()


        # 识别本地文件
        if self.mode == "zh":
            result = client.asr(data, 'wav', 16000, {
                'dev_pid': 1536,
            })
        else:
            result = client.asr(data, 'wav', 16000, {
                'dev_pid': 1737,
            })
        if result["err_no"] == 0 and result["err_msg"] == "success.":
            line = " ".join(result["result"])
            if self.mode == "zh":

                result = client.synthesis("你说了" + line, self.mode, 1, {
                    'vol': 5,
                    'per': 1
                })
            else:
                result = client.synthesis("you said" + line, "zh", 1, {
                    'vol': 5,
                    'per': 1
                })
            prepared = save_synthesis("temp", result)
            if prepared:
                play_sound("temp/temp.wav")
            else:
                play_sound("temp/recoginition_failed.wav")
            self.no_audio_times = 0
            success = self.process_once(line)
            return success
        elif result["err_no"] == 3300 or result["err_no"] == 3301 or result["err_no"] == 3302:
            play_sound("temp/no_sound.wav")
            self.no_audio_times += 1
            if self.no_audio_times > 2:
                self.sleep(1)
                play_sound("temp/no_sound_annoy.wav")
                self.quit_signal.emit()
                self.terminate()
            else:
                return True
        else:
            self.no_audio_times = 0
            play_sound("temp/recoginition_failed.wav")
            return True


class MainRecognizingThread(QThread):
    prepare_signal = pyqtSignal(bool)

    def __init__(self, window):
        super().__init__()
        self.voiceThread = None
        self.prepared = None
        self.window = window

    def run(self) -> None:
        self.sleep(3)
        # welcoming
        self.prepare()
        # background recognizing
        self.voiceThread = VoiceThread()
        self.voiceThread.quit_signal.connect(self.window.close_window)
        self.voiceThread.color_signal.connect(self.window.change_color)
        self.voiceThread.mode_signal.connect(self.window.change_mode)
        self.voiceThread.start()
        self.voiceThread.wait()

    def greeting(self) -> None:
        pass

    def prepare(self):
        if not os.path.exists("temp"):
            os.mkdir("temp")
        self.prepared = True
        result = client.synthesis('你好呀呀呀呀呀,冲冲冲', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
        self.prepared = save_synthesis("hello", result)
        result = client.synthesis('滴滴', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("begin_listening", result)
        result = client.synthesis('咋办，我没听懂你说了啥, 你要不再说一次', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("recoginition_failed", result)
        result = client.synthesis('你咋不说话呢, 麦坏了', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("no_sound", result)
        result = client.synthesis('哼,一直不说话,拜拜了您馁', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("no_sound_annoy", result)
        result = client.synthesis('巴啦啦魔法变身，英文模式', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("chinese_to_english", result)
        result = client.synthesis('papa mamamiya sakura ohno，中文模式', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("english_to_chinese", result)
        result = client.synthesis('好的，立马唤醒大哥', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("open_siri", result)
        result = client.synthesis('好的，你先听着歌，我歇会', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("play_music", result)
        result = client.synthesis('诶，你喊我呢，啥事儿啊', 'zh', 1, {
            'vol': 5,
            'per': 1
        })
        self.prepared = save_synthesis("wake_up", result)
        result = client.synthesis('拜拜', 'zh', 1, {
            'vol': 7,
            'per': 1,
            'spd': 3
        })
        self.prepared = save_synthesis("quit", result)
        result = client.synthesis('你好呀呀呀呀呀,冲冲冲,和我聊天吧', 'zh', 1, {
            'vol': 5,
            'spd': 6,
            'per': 1
        })
        self.prepared = save_synthesis("baigei", result)
        if self.prepared:
            playSoundThread = PlaySoundThread("temp/baigei.wav")
            playSoundThread.start()
            self.sleep(3)
            self.prepare_signal.emit(True)
            playSoundThread.wait()
        else:
            self.prepare_signal.emit(False)


class PlaySoundThread(QThread):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def run(self) -> None:
        play_sound(self.filename)

