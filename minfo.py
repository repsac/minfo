# MIT License
#
# Copyright (c) 2019 Ed Caspersen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# allcopies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
Use as a standard Python API
>>> minfo = MInfo('EXAMPLE.MOV')
>>> minfo.focal_length
80.0 mm
>>> minfo.exif['Focus Mode']
Manual
>>> minfo.streams['r_frame_rate']
30000/1001

--------
If executed from a shell, print the values of any of the known properties
or keys values (from either exif or first stream index).
> python -m minfo EXAMPLE.MOV -p focal_length,iso -k "Focus Mode"
EXAMPLE.MOV
        focal_length: 80.0 mm
        iso: 100.0
        Focus Mode: Manual
"""
import os
import json
import argparse
import tempfile
from subprocess import PIPE, Popen


class MInfo(object):

    def __init__(self, path):
        self.path = path
        self.exif = None
        self.streams = None
        self._setup()
    
    def _setup(self):
        self.exif = _exiftool(self.path)
        probe = _ffprobe(self.path)
        self.streams = probe['streams']
        self.format = probe['format']

    @property
    def resolution(self):
        xres = _find_data(self,
                          ('Source Image Width', 'width'))
        yres = _find_data(self,
                          ('Source Image Height', 'height'))
        resolution = tuple([xres, yres])
        if resolution != (None, None):
            return resolution
    
    @property
    def fps(self):
        return _find_data(self,
                          ('Video Frame Rate', 'r_frame_rate'))

    @property
    def duration(self):
        duration = _find_data(self, ('Duration', 'duration'))
        if duration is not None and 's' in duration:
            duration = float(duration[:-1])
        return duration

    # properties below this comment do not have unit tests
    @property
    def camera_model(self):
        return _find_data(self, ('Camera Model Name', None))

    @property
    def camera_lens(self):
        return _find_data(self, ('Lens Type', None))

    @property
    def aperture(self):
        return _find_data(self, ('Aperture', None))

    @property
    def focal_length(self):
        return _find_data(self, ('Focal Length', None))

    @property
    def iso(self):
        return _find_data(self, ('ISO', None))

    @property
    def shutter_speed(self):
        return _find_data(self, ('Shutter Speed', None))

    @property
    def color_temp(self):
        return _find_data(self, ('Color Temp Kelvin', None))

    @property
    def white_balance(self):
        return _find_data(self, ('White Balance', None))


def _find_data(minfo, keys, stream_index=0):
    data = _exif_data(minfo, keys[0])

    if data is None:
        data = _stream_data(minfo, stream_index, keys[1])

    return data


def _exif_data(minfo, key):
    for exif_key, exif_value in minfo.exif:
        if exif_key == key:
            return exif_value


def _stream_data(minfo, stream_index, key):
    try:
        stream = minfo.streams[stream_index]
    except IndexError:
        data = None
    else:
        data = stream.get(key)
    return data


def _exif_parser(data):
    exif_data = []
    for line in str(data).split('\n'):
        index = line.find(':')
        key = line[:index].strip()
        value = line[index+1:].strip()
        for typ in (int, float):
            try:
                value = typ(value)
            except ValueError:
                pass
        exif_data.append((key, value))
    return tuple(exif_data)


def _exiftool(path):
    return _exec_tool('exiftool "%s"', path, _exif_parser)


def _ffprobe(path):
    command = 'ffprobe.exe -v quiet -print_format json -show_format -show_streams "%s"'
    return _exec_tool(command, path, json.loads)


def _exec_tool(command, path, func):
    data = _subproc(command % path)
    return func(data)


def _subproc(command):
    proc = Popen(command, stdout=PIPE, encoding='utf8')
    out = proc.communicate()[0]
    return out


def _unittest():

    def set_up():

        def generate_media(command, media):
            _subproc(command)
            if not os.path.exists(media):
                raise IOError("Failed to generate media '%s'" % media)

        wav = tempfile.mktemp(suffix='.wav')
        sox = 'sox -V0 -r 48000 -n -b 16 -c 2 %s synth 10 sin 1000 vol -10dB' % wav
        generate_media(sox, wav)
        mov = tempfile.mktemp(suffix='.mov')
        ffmpeg = 'ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 '\
                 ' %s -i %s -hide_banner -loglevel panic' % (mov, wav)
        
        try:
            generate_media(ffmpeg, mov)
        except IOError:
            os.remove(wav)

        return (MInfo(mov), MInfo(wav))

    def _cleanup(files):
        for each in files:
            if os.path.exists(each):
                os.remove(each)

    mov, wav = set_up()

    def test_attributes(minfo):
        assert isinstance(minfo.exif, tuple), "exif data is not a tuple"
        assert isinstance(minfo.streams, list), "streams data is not a list"
        assert isinstance(minfo.format, dict), "format data is not a dict"

    def test_movie_data(minfo):
        assert minfo.resolution == (1280, 720), "resolution is %s" % str(minfo.resolution)
        assert minfo.fps == 30, "fps is %s" % str(minfo.fps)
        assert minfo.duration == 10.02, "duration is %s" % str(minfo.duration)

    def test_audio_data(minfo):
        assert minfo.resolution == None, "resolution is %s" % str(minfo.resolution)
        assert minfo.fps == '0/0', "fps is %s" % str(minfo.fps)
        assert minfo.duration == 10.0, "duration is %s" % str(minfo.duration)

    try:
        test_attributes(mov)
        test_movie_data(mov)
        test_audio_data(wav)
        test_audio_data(wav)
    except:
        _cleanup((mov.path, wav.path))
        raise


def _print_data(files, properties, keys):
    for fi in files:
        minfo = MInfo(fi)
        print(minfo.path)
        for prop in properties:
            if hasattr(minfo, prop):
                print("\t%s: %s" % (prop, str(getattr(minfo, prop))))
        for key in keys:
            value = _find_data(minfo, (key, key))
            print("\t%s: %s" % (key, value))


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*')
    parser.add_argument('-u', '--unittest', action='store_true')
    parser.add_argument('-p', '--property')
    parser.add_argument('-k', '--key')
    args = parser.parse_args()
    if args.unittest:
        _unittest()
    elif args.files:
        properties = [] if not args.property else args.property.split(',')
        keys = [] if not args.key else args.key.split(',')
        _print_data(args.files, properties, keys)


if __name__ == '__main__':
    _main()