
import azure.cognitiveservices.speech as speechsdk
import datetime

speech_key = "YOUR_KEY"
service_region = "YOUR_REGION"
speech_config = speechsdk.SpeechConfig(
    subscription=speech_key, region=service_region)
speech_config.set_property(
    property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestSentenceBoundary, value='true')
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

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

    def get_ssml(self, text):
        return SSML_TEMPLATE.format(
            language=self.language,
            speaker=self.speaker,
            style=self.style,
            rate=self.rate,
            pitch=self.pitch,
            text=text
        ).strip()

    def get_result(self, text):
        ssml_string = self.get_ssml(text)
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config)
        speech_synthesis_result = speech_synthesizer.speak_ssml_async(
            ssml_string).get()
        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized for text [{}]".format(text))
            if self.output:
                stream = speechsdk.AudioDataStream(speech_synthesis_result)
                stream.save_to_wav_file(self.output)
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print("Speech synthesis canceled: {}".format(
                cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details: {}".format(
                        cancellation_details.error_details))
                    print("Did you set the speech resource key and region values?")
