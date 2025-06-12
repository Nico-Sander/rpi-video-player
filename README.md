# Raspberry Pi Video Player für Mik und co.
## Todo
- [ ] downgrade Pi to Pi OS Legacy (buster) to get access to `omxplayer`
- [ ] clone this repo to the Pi
- [ ] write simple program that plays video using `omxplayer`

## Notes
- Video should be in the following format: H264 MPEG4 with 1080p resolution
  - Can be done with vlc player: Media > Convert > Select video file > Select profile: Video - H.264 + MP3 (MP4)
 
## Documentation
1. Flashed Raspberry Pi 1 B+ with older, `buster`-based Raspberry Pi OS (https://downloads.raspberrypi.org/raspbian/images/raspbian-2020-02-14/) because new ones don't support the lightweight terminal videoplayer `omxplayer` anymore.
2. Made sure some basic dependencies like python3 and git were installed.
3. Downloaded a [test video](test_video_converted.mp4) from a stock site and converted it to H264 MPEG4 because `omxplayer` is optimized for it.
4. Synced the test video to the Pi using git.
