#!/usr/bin/env python3
import sys
import ctypes
from proto.soda_api_pb2 import ExtendedSodaConfigMsg, SodaResponse, SodaRecognitionResult
import os
from enum import Enum
import argparse
import time
from rich.live import Live
from rich.console import Console
from rich.text import Text

from config import CHANNEL_COUNT, SAMPLE_RATE, CHUNK_SIZE, SODA_PATH

CALLBACK = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_byte), ctypes.c_int, ctypes.c_void_p)
class SodaConfig(ctypes.Structure):
    _fields_ = [('soda_config', ctypes.c_char_p),
                ('soda_config_size', ctypes.c_int),
                ('callback', CALLBACK),
                ('callback_handle', ctypes.c_void_p)]

class SodaLanguage(Enum):
    CHINESE_HANS = "cmn-Hans-CN"
    CHINESE_HANT = "cmn-Hant-TW"
    GERMAN = "de-DE"
    ENGLISH = "en-US"
    FRENCH = "fr-FR"
    HINDI = "hi-IN"
    INDONESIAN = "id-ID"
    ITALIAN = "it-IT"
    JAPANESE = "ja-JP"
    KOREAN = "ko-KR"
    POLISH = "pl-PL"
    PORTUGUESE = "pt-BR"
    THAI = "th-TH"
    TURKISH = "tr-TR"

class SodaClient():
    def __init__(self, callback=None, language=SodaLanguage.ENGLISH):
        self.sodalib = ctypes.CDLL(SODA_PATH)
        if callback == None:
            callback = CALLBACK(self.resultHandler)
        else:
            callback = CALLBACK(callback)
        cfg_proto = ExtendedSodaConfigMsg()
        cfg_proto.channel_count = CHANNEL_COUNT
        cfg_proto.sample_rate = SAMPLE_RATE
        cfg_proto.api_key = 'ce04d119-129f-404e-b4fe-6b913fffb6cb'
        cfg_proto.recognition_mode = ExtendedSodaConfigMsg.CAPTION
        cfg_proto.language_pack_directory = f'./models/{language.value}/SODAModels/'
        cfg_serialized = cfg_proto.SerializeToString()
        self.config = SodaConfig(cfg_serialized, len(cfg_serialized), callback, None)
        self.sodalib.CreateExtendedSodaAsync.restype = ctypes.c_void_p
        self.console = Console()
        self.live = Live("", console=self.console, refresh_per_second=10)
        
    def start(self):
        self.handle = ctypes.c_void_p(self.sodalib.CreateExtendedSodaAsync(self.config))
        self.sodalib.ExtendedSodaStart(self.handle)
        with self.live:  # start the live display
            with open(self.audio_file, "rb") as f:
                chunk = f.read(CHUNK_SIZE)
                while chunk:
                    self.sodalib.ExtendedAddAudio(self.handle, chunk, len(chunk))
                    # emulate stream delay, can be adjusted, though I've found lower numbers cause issues.
                    time.sleep(0.005)  
                    chunk = f.read(CHUNK_SIZE)
        print("\n\n")

    def delete(self):
        self.sodalib.DeleteExtendedSodaAsync(self.handle)

    def resultHandler(self, response, rlen, instance):
        res = SodaResponse()
        res.ParseFromString(ctypes.string_at(response, rlen))
        if res.soda_type == SodaResponse.SodaMessageType.RECOGNITION:
            if res.recognition_result.result_type == SodaRecognitionResult.ResultType.FINAL:
                # print final results normally
                self.console.print(f'[green]* final:[/green] {res.recognition_result.hypothesis[0]}')
            elif res.recognition_result.result_type == SodaRecognitionResult.ResultType.PARTIAL:
                # update the live display for partial results
                text = Text.from_markup(f'[yellow]* partial:[/yellow] {res.recognition_result.hypothesis[0]}')
                self.live.update(text)
                
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run SODA client with specified language',
        formatter_class=argparse.RawTextHelpFormatter
    )
    languages = [lang.name.lower() for lang in SodaLanguage]
    parser.add_argument('-l', '--language', 
                       type=str.lower,
                       choices=languages,
                       default='english',
                       metavar='LANG',
                       help='Language to use. Available languages:\n' + 
                            '\n'.join(f'  - {lang}' for lang in languages))
    parser.add_argument('-p', '--properties',
                       action='store_true',
                       help='Print audio file properties')
    parser.add_argument('audio_file', help='Path to the audio file to process')
    args = parser.parse_args()

    # convert string argument to SodaLanguage enum
    selected_language = SodaLanguage[args.language.upper()]
    
    # check if audio file exists
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file not found at {args.audio_file}")
        sys.exit(1)

    # check if language models exist
    language_model_path = f'./models/{selected_language.value}/SODAModels/'
    if not os.path.exists(language_model_path):
        print(f"Error: Language models not found at {language_model_path}")
        print("Please download the required language models first.")
        sys.exit(1)

    # check if SODA binary exists
    if not os.path.exists(SODA_PATH):
        print(f"Error: SODA binary not found at {SODA_PATH}")
        sys.exit(1)

    # check audio file properties using wave module if requested
    if args.properties:
        import wave
        with wave.open(args.audio_file, 'rb') as wav_file:
            print(f"Audio file properties:")
            print(f"Sample rate: {wav_file.getframerate()} Hz")
            print(f"Channels: {wav_file.getnchannels()}")

    # redirect stderr to /dev/null
    stderr_fd = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)

    client = SodaClient(language=selected_language)
    client.audio_file = args.audio_file
    try:
        client.start()
    except KeyboardInterrupt:
        client.delete()
    finally:
        # restore stderr
        os.dup2(stderr_fd, 2)
        os.close(stderr_fd)