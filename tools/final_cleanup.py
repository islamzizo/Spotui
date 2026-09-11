from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
ps=ROOT/'app/src/main/java/com/music/spotui/ui/notification/PlaybackService.kt'
s=ps.read_text()
s=s.replace('import com.music.spotui.di.SpotifyWebPlayer\n','')
s=re.sub(r'\n\s*private var webPlayer: WebMediaPlayer\? = null\n\s*private var showingWeb = false\n','\n',s)
s=re.sub(r'\n\s*webPlayer = WebMediaPlayer\(mainLooper, currentSongState\) \{ forward -> advance\(forward\) \}\n','\n',s)
s=re.sub(r'\n\s*// When a crossfade promotes a new ExoPlayer instance, re-bind the session to it\n\s*// \(runs on the main thread; setPlayer is the supported way to swap a session\'s player\.\)\n\s*SongPlayer\.onPlayerSwapped = \{ newPlayer ->\n\s*if \(!showingWeb\) mediaSession\?\.player = wrap\(newPlayer\)\n\s*\}\n','\n',s)
s=re.sub(r'\n\s*// As the hidden web player streams,.*?SpotifyWebPlayer\.onStateChanged = \{.*?\n\s*\}\n\s*\}\n','\n',s,flags=re.S)
s=re.sub(r'\n\s*/\*\* Point the media session at whichever engine is currently producing audio\. \*/\n\s*private fun syncSessionPlayer\(\) \{.*?\n\s*\}\n','\n',s,flags=re.S)
s=s.replace('syncSessionPlayer()','')
ps.write_text(s)
for p in [ROOT/'app/src/main/java/com/music/spotui/di/SpotifyWebPlayer.kt',ROOT/'app/src/main/java/com/music/spotui/ui/notification/WebMediaPlayer.kt']:
    if p.exists(): p.unlink()
for p in [ROOT/'.github/workflows/migrate-monochrome.yml',ROOT/'.github/workflows/monochrome-ci.yml',ROOT/'tools/final_cleanup.py']:
    pass
forbidden=('youtube','deezer','soundcloud','spotiflac','spotifywebplayer','webmediaplayer')
for p in ROOT.rglob('*'):
    if not p.is_file() or '.git' in p.parts or 'build' in p.parts: continue
    try: text=p.read_text(errors='ignore').lower()
    except Exception: continue
    if any(x in text for x in forbidden):
        raise SystemExit(f'forbidden playback reference remains: {p}')
print('cleanup ok')
