import os
import tempfile
import minfo


def _generate_media(command, media):
    minfo._subproc(command)
    if not os.path.exists(media):
        raise IOError("Failed to generate media '%s'" % media)


def _set_up():
    wav = tempfile.mktemp(suffix='.wav')
    sox = 'sox -V0 -r 48000 -n -b 16 -c 2 %s synth 10 sin 1000 vol -10dB' % wav
    _generate_media(sox, wav)
    mov = tempfile.mktemp(suffix='.mov')
    ffmpeg = 'ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 '\
             ' %s -i %s -hide_banner -loglevel panic' % (mov, wav)
    
    try:
        _generate_media(ffmpeg, mov)
    except IOError:
        os.remove(wav)

    return (minfo.MInfo(mov), minfo.MInfo(wav))

def _cleanup(files):
    for each in files:
        if os.path.exists(each):
            os.remove(each)

def _test_attributes(minfo):
    assert isinstance(minfo.exif, tuple), "exif data is not a tuple"
    assert isinstance(minfo.streams, list), "streams data is not a list"
    assert isinstance(minfo.format, dict), "format data is not a dict"


def _test_movie_data(minfo):
    assert minfo.resolution == (1280, 720), "resolution is %s" % str(minfo.resolution)
    assert minfo.fps == 30, "fps is %s" % str(minfo.fps)
    assert minfo.duration == 10.02, "duration is %s" % str(minfo.duration)


def _test_audio_data(minfo):
    assert minfo.resolution == None, "resolution is %s" % str(minfo.resolution)
    assert minfo.fps == '0/0', "fps is %s" % str(minfo.fps)
    assert minfo.duration == 10.0, "duration is %s" % str(minfo.duration)


def _unittest():
    
    mov, wav = _set_up()

    try:
        _test_attributes(mov)
        _test_movie_data(mov)
        _test_audio_data(wav)
        _test_audio_data(wav)
    except:
        _cleanup((mov.path, wav.path))
        raise


def _main():
    _unittest()


if __name__ == '__main__':
    _main()