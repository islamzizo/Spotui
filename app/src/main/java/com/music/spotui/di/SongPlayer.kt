package com.music.spotui.di

import android.content.Context
import android.net.Uri
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.MimeTypes
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import com.music.spotui.data.entity.SongsModel
import com.music.spotui.data.preferences.addDownload
import com.music.spotui.data.preferences.downloadedPathForQuery
import com.music.spotui.data.preferences.isDownloaded
import kotlinx.coroutines.*
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ConcurrentHashMap

/** Native Media3 playback using Monochrome as the sole online audio backend. */
object SongPlayer {
    private const val PREFIX = "spotify:track:"
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val cache = ConcurrentHashMap<String, String>()
    private val qualityCache = ConcurrentHashMap<String, String>()
    private val downloading = ConcurrentHashMap.newKeySet<String>()
    private val progress = ConcurrentHashMap<String, Int>()
    private val downloadingSongs = ConcurrentHashMap<String, SongsModel>()
    private var player: ExoPlayer? = null
    private var currentRequest = ""
    private var restoreQuery: String? = null
    private var restorePosition = 0L
    private var title = ""
    private var artist = ""
    private var cover = ""

    @Volatile var currentSource = "Monochrome"
        private set
    @Volatile var currentQuality = ""
        private set
    @Volatile var onStreamFailed: ((String) -> Unit)? = null
    @Volatile var onDownloadsChanged: (() -> Unit)? = null
    @Volatile var lastDownloadError: String? = null
    @Volatile var onPlayerSwapped: ((ExoPlayer) -> Unit)? = null

    val exoPlayer: ExoPlayer? get() = player
    val isPlaying: Boolean get() = player?.isPlaying == true
    val currentPosition: Long get() = player?.currentPosition ?: 0L
    val duration: Long get() = player?.duration?.takeIf { it > 0 } ?: 0L

    fun ensureCreated(context: Context): ExoPlayer {
        if (player == null) {
            player = ExoPlayer.Builder(context.applicationContext).build().also { p ->
                p.addListener(object : Player.Listener {
                    override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                        cache.remove(currentRequest)
                        onStreamFailed?.invoke(currentRequest)
                    }
                })
            }
        }
        return player!!
    }

    fun bindState(state: CurrentSongState) = Unit
    fun setNowPlayingMeta(t: String, a: String, c: String) { title=t; artist=a; cover=c }
    fun buildSpotifyPlayQuery(id: String, t: String, a: String): String = if (id.isBlank()) "$t $a" else "$PREFIX$id|$t $a"
    fun registerLossless(pairs: List<Pair<String,String>>) = Unit
    fun registerAlternativeKeys(pairs: List<Pair<String,String>>) = Unit
    fun registerExplicit(pairs: List<Pair<String,Boolean>>) = Unit
    fun registerDuration(pairs: List<Pair<String,Int>>) = Unit
    data class TrackMatchMetadata(val title:String,val artist:String,val album:String,val isrc:String="")
    fun registerMetadata(pairs: List<Pair<String,TrackMatchMetadata>>) = Unit
    fun invalidateResolvedStream(song:String){cache.remove(song);qualityCache.remove(song)}
    fun setRestorePoint(query:String, positionMs:Long){restoreQuery=query;restorePosition=positionMs}

    fun playSong(song: String, context: Context) {
        val app=context.applicationContext
        currentRequest=song
        val p=ensureCreated(app); p.pause(); p.clearMediaItems()
        downloadedPathForQuery(app,song)?.let { path ->
            currentSource="Downloaded"; currentQuality=path.substringAfterLast('.',"").uppercase()
            setMedia(Uri.fromFile(File(path)).toString(),app,false); return
        }
        if(song.startsWith("content://")||song.startsWith("file://")){
            currentSource="Local"; currentQuality=""
            setMedia(song,app,false); return
        }
        scope.launch {
            val resolved=runCatching{MonochromeClient.resolveSpotifyQuery(song)}.getOrNull()
            if(currentRequest!=song)return@launch
            if(resolved==null){withContext(Dispatchers.Main){onStreamFailed?.invoke(song);android.widget.Toast.makeText(app,"Monochrome couldn't find a playable stream",android.widget.Toast.LENGTH_SHORT).show()};return@launch}
            cache[song]=resolved.url;qualityCache[song]=resolved.qualityLabel;currentSource="Monochrome";currentQuality=resolved.qualityLabel
            withContext(Dispatchers.Main){if(currentRequest==song)setMedia(resolved.url,app,resolved.isDash)}
        }
    }

    private fun setMedia(url:String,context:Context,dash:Boolean){
        val item=MediaItem.Builder().setUri(url).setMediaMetadata(MediaMetadata.Builder().setTitle(title).setArtist(artist).apply{if(cover.isNotBlank())setArtworkUri(Uri.parse(cover))}.build()).apply{if(dash)setMimeType(MimeTypes.APPLICATION_MPD)}.build()
        val p=ensureCreated(context);p.setMediaItem(item);p.prepare()
        if(currentRequest==restoreQuery&&restorePosition>0)p.seekTo(restorePosition)
        restoreQuery=null;restorePosition=0;p.playWhenReady=true
    }

    fun play(){player?.play()};fun pause(){player?.pause()};fun togglePlayPause(){if(isPlaying)pause()else play()}
    fun seekTo(ms:Long){player?.seekTo(ms.coerceAtLeast(0))};fun seekForward(){player?.seekForward()};fun seekBack(){player?.seekBack()};fun stop(){player?.stop()}
    fun prefetch(song:String,context:Context){if(song.isBlank()||cache.containsKey(song))return;scope.launch{MonochromeClient.resolveSpotifyQuery(song)?.let{cache[song]=it.url;qualityCache[song]=it.qualityLabel}}}
    fun prefetchList(songs:List<String>,context:Context,count:Int=4){songs.take(count).forEach{prefetch(it,context)}}
    fun webPlaybackActive()=false

    fun isDownloading(q:String)=downloading.contains(q)
    fun downloadProgress(q:String)=progress[q]?:-1
    fun downloadingSnapshot()=downloadingSongs.entries.map{it.value to(progress[it.key]?:0)}
    fun allDownloaded(songs:List<SongsModel>,context:Context)=songs.isNotEmpty()&&songs.all{isDownloaded(context,it.id.toString())}
    fun downloadAll(songs:List<SongsModel>,context:Context)=songs.forEach{downloadSong(it,context)}

    fun downloadSong(song:SongsModel,context:Context,onComplete:(Boolean)->Unit={}){
        val app=context.applicationContext;if(song.url.isBlank()||isDownloaded(app,song.id.toString())||!downloading.add(song.url))return
        downloadingSongs[song.url]=song;progress[song.url]=0;onDownloadsChanged?.invoke()
        scope.launch{
            val ok=runCatching{downloadToFile(song,app)}.getOrDefault(false)
            downloading.remove(song.url);downloadingSongs.remove(song.url);progress.remove(song.url)
            withContext(Dispatchers.Main){onDownloadsChanged?.invoke();onComplete(ok)}
        }
    }

    private suspend fun downloadToFile(song:SongsModel,app:Context):Boolean{
        val r=MonochromeClient.resolveSpotifyQuery(song.url)?:run{lastDownloadError="Monochrome could not resolve the track";return false}
        val dir=File(app.filesDir,"downloads").apply{mkdirs()};val out=File(dir,"${song.id}.flac");val tmp=File(dir,"${song.id}.part")
        val ok=if(r.isDash)MonochromeClient.downloadDashToFlac(r.url,tmp,song.url,progress) else ranged(r.url,tmp,song.url)
        if(!ok){tmp.delete();return false};if(!tmp.renameTo(out)){tmp.delete();return false};addDownload(app,song,out.absolutePath);return true
    }

    private fun ranged(url:String,out:File,q:String):Boolean{
        val c=(URL(url).openConnection() as HttpURLConnection).apply{connectTimeout=15000;readTimeout=30000;instanceFollowRedirects=true;setRequestProperty("User-Agent","Spotui/Monochrome Android")}
        return try{if(c.responseCode !in 200..299)return false;val total=c.contentLengthLong;c.inputStream.use{i->out.outputStream().buffered().use{o->{val b=ByteArray(65536);var n=0L;while(true){val r=i.read(b);if(r<0)break;o.write(b,0,r);n+=r;if(total>0)progress[q]=((n*100)/total).toInt().coerceIn(0,100)}}}};progress[q]=100;true}catch(e:Exception){lastDownloadError=e.message;false}finally{c.disconnect()}
    }
    fun release(){player?.release();player=null}
}
