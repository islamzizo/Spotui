from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
ps=ROOT/'app/src/main/java/com/music/spotui/ui/notification/PlaybackService.kt'
s=ps.read_text()
s=s.replace('import com.music.spotui.di.SpotifyWebPlayer\n','')
s=re.sub(r'\n\s*private var webPlayer: WebMediaPlayer\? = null\n\s*private var showingWeb = false\n','\n',s)
s=re.sub(r'\n\s*webPlayer = WebMediaPlayer\(mainLooper, currentSongState\) \{ forward -> advance\(forward\) \}\n','\n',s)
s=re.sub(r'\n\s*// When a crossfade promotes a new ExoPlayer instance.*?SongPlayer\.onPlayerSwapped = \{.*?\n\s*\}\n','\n',s,flags=re.S)
s=re.sub(r'\n\s*// As the hidden web player streams,.*?SpotifyWebPlayer\.onStateChanged = \{.*?\n\s*\}\n\s*\}\n','\n',s,flags=re.S)
s=re.sub(r'\n\s*/\*\* Point the media session at whichever engine is currently producing audio\. \*/.*?private fun syncSessionPlayer\(\) \{.*?\n\s*\}\n','\n',s,flags=re.S)
s=s.replace('syncSessionPlayer()','')
ps.write_text(s)
for p in [ROOT/'app/src/main/java/com/music/spotui/di/SpotifyWebPlayer.kt',ROOT/'app/src/main/java/com/music/spotui/ui/notification/WebMediaPlayer.kt']:
    if p.exists(): p.unlink()
print('cleanup ok')
