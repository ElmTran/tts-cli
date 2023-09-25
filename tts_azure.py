from convert import Converter
import argparse

DEFAULT_SETTINGS = {
    "language": "en-US",
    "speaker": "en-US-JennyNeural",
    "style": "chat",
    "rate": "0%",
    "pitch": "0%",
    "output": None,
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", type=str,
                        dest="language", help="language")
    parser.add_argument("--speaker", type=str, dest="speaker", help="speaker")
    parser.add_argument("--style", type=str, dest="style", help="speech style")
    parser.add_argument("--rate", type=str, dest="rate",
                        help="perception rate negative is slow")
    parser.add_argument("--pitch", type=str, dest="pitch",
                        help="perception pitch")
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
    converter.get_result(text)
