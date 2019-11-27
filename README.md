# minfo
Python wrapper for extracting data from ffprobe and exiftool (read only)

Use as a standard Python API
```
>>> minfo = MInfo('EXAMPLE.MOV')
>>> minfo.focal_length
80.0 mm
>>> minfo.exif['Focus Mode']
Manual
>>> minfo.streams['r_frame_rate']
30000/1001
```

If executed from a shell, print the values of any of the known properties
or keys values (from either exif or first stream index).
```
> python -m minfo EXAMPLE.MOV -p focal_length,iso -k "Focus Mode"
EXAMPLE.MOV
        focal_length: 80.0 mm
        iso: 100.0
        Focus Mode: Manual
```