import websockets
import requests
import re
import asyncio
import uuid
import argparse
from datetime import datetime
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO


AZURE_TEST_URL = "https://azure.microsoft.com/zh-cn/products/cognitive-services/speech-translation/"
AZURE_WSS_API = "wss://eastus.api.speech.microsoft.com/cognitiveservices/websocket/v1"
SSML_TEMPLATE = """
<speak xmlns="http://www.w3.org/2001/10/synthesis"
        xmlns:mstts="http://www.w3.org/2001/mstts"
        xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="{language}">
        <voice name="{speaker}">
            <mstts:express-as  style="{style}" >
                <prosody rate="{rate}" pitch="{pitch}">
                {text}
                </prosody>
            </mstts:express-as>
        </voice>
</speak>
"""
DEFAULT_SETTINGS = {
    "language": "en-US",
    "speaker": "en-US-DavisNeural",
    "style": "chat",
    "rate": "0%",
    "pitch": "0%",
    "output": None,
}


def get_x_time():
    return datetime.now().isoformat()


class Converter:
    def __init__(self, language, speaker, style, rate, pitch, output):
        self.language = language
        self.speaker = speaker
        self.style = style
        self.rate = rate
        self.pitch = pitch
        self.output = output
        self.token = None

    def get_token(self):
        if not self.token:
            resp = requests.get(AZURE_TEST_URL)
            reg = re.compile(r"token: \"(.*?)\"")
            match = reg.findall(resp.text)
            if match:
                self.token = "bearer20%" + match[0]
            else:
                raise Exception("get token failed")
        return self.token

    def get_ssml(self, text):
        return SSML_TEMPLATE.format(
            language=self.language,
            speaker=self.speaker,
            style=self.style,
            rate=self.rate,
            pitch=self.pitch,
            text=text
        ).strip()

    def make_payloads(self, text):

        return [
            {
                'path': 'speech.config',
                'content_type': 'application/json',
                'content': '''
                        {"context":{"system":{"name":"SpeechSDK","version":"1.19.0","build":"JavaScript","lang":"JavaScript","os":{"platform":"Browser/Linux x86_64","name":"Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0","version":"5.0 (X11)"}}}}
                        '''
            },
            {
                'path': 'speech.synthesis',
                'content_type': 'application/json',
                'content': '''
                        {"synthesis":{"audio":{"metadataOptions":{"sentenceBoundaryEnabled":false,"wordBoundaryEnabled":false},"outputFormat":"audio-16khz-32kbitrate-mono-mp3"}}}
                        '''
            },
            {
                'path': 'ssml',
                'content_type': 'application/ssml+xml',
                'content': self.get_ssml(text)
            }
        ]

    async def exec(self, text):
        payloads = self.make_payloads(text)
        Authorization = self.get_token()
        XConnectionId = uuid.uuid4().hex.upper()
        endpoint = f"{AZURE_WSS_API}?TrafficType=AzureDemo&Authorization={Authorization}&X-ConnectionId={XConnectionId}"
        hearders = {'Origin': 'https://azure.microsoft.com'}
        async with websockets.connect(endpoint, extra_headers=hearders) as ws:
            for payload in payloads:
                msg = f"Path: {payload['path']}\r\nX-RequestId: {XConnectionId}\r\nX-Timestamp: {get_x_time()}\r\nContent-Type: {payload['content_type']}\r\n\r\n{payload['content'].strip()}"
                await ws.send(msg)
            end_pattern = re.compile("Path:turn.end")
            audio = b''
            async for resp in ws:
                if not end_pattern.search(str(resp)):
                    # check if resp type is audio bytes
                    if isinstance(resp, bytes):
                        try:
                            needle = b'Path:audio\r\n'
                            start_idx = resp.find(needle) + len(needle)
                            audio += resp[start_idx:]
                        except:
                            pass
                else:
                    break

            segment = AudioSegment.from_file(BytesIO(audio), format="mp3")
            play(segment)
            if self.output:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                segment.export(f"{self.output}/{timestamp}.mp3", format="mp3")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", type=str,
                        dest="language", help="language")
    parser.add_argument("--speaker", type=str, dest="speaker", help="speaker")
    parser.add_argument("--style", type=str, dest="style", help="speech style")
    parser.add_argument("--rate", type=str, dest="rate", help="perception rate negative is slow")
    parser.add_argument("--pitch", type=str, dest="pitch", help="perception pitch")
    parser.add_argument("--text", type=str, dest="text", help="text to speech")
    parser.add_argument("--file", type=str, dest="file", help="file to speech")
    parser.add_argument("--output", type=str, dest="output", help="output dir")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    setting = DEFAULT_SETTINGS.copy()
    for k, v in vars(args).items():
        if k in setting and v:
            setting[k] = v
    converter = Converter(**setting)

    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    else:
        text = args.text
    asyncio.get_event_loop().run_until_complete(converter.exec(text))
