from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def remove(path):
    p = ROOT / path
    if p.is_dir():
        shutil.rmtree(p)
    elif p.exists():
        p.unlink()


def replace(path, old, new):
    p = ROOT / path
    s = p.read_text(encoding='utf-8')
    if old not in s:
        raise SystemExit(f'pattern not found in {path}: {old[:100]!r}')
    p.write_text(s.replace(old, new), encoding='utf-8')


# --- Remove source-specific modules/files ---
remove('innertube')
remove('app/src/main/java/com/music/spotui/deezer')
remove('app/src/main/java/com/music/spotui/lossless')
remove('app/src/main/java/com/music/spotui/di/SpotifyWebPlayer.kt')
remove('app/src/main/java/com/music/spotui/ui/notification/WebMediaPlayer.kt')
for name in [
    'DeezerPref.kt', 'SpotiflacSessionPref.kt', 'AlternativeStreamPref.kt',
]:
    remove('app/src/main/java/com/music/spotui/data/preferences/' + name)
for name in ['DeezerLoginScreen.kt', 'DeezerIntroScreen.kt', 'YouTubeLoginScreen.kt', 'SpotiflacVerifyScreen.kt']:
    remove('app/src/main/java/com/music/spotui/ui/screens/' + name)
remove('spotify/src/main/kotlin/com/metrolist/spotify/SpotiFlac.kt')

# --- Gradle/module cleanup ---
replace('settings.gradle.kts', 'include(":innertube")\n ', ' ')
app_gradle = ROOT / 'app/build.gradle.kts'
s = app_gradle.read_text(encoding='utf-8')
s = s.replace('    // Spotify metadata + YouTube streaming, ported from Meld (replaces Firebase data layer)\n', '    // Spotify metadata layer\n')
s = s.replace('    implementation(project(":innertube"))\n', '')
s = s.replace('    //okhttp + timber (used by the ported YouTube streaming flow)\n', '    // HTTP + logging\n')
app_gradle.write_text(s, encoding='utf-8')

# --- Manifest: MediaStore audio permission ---
replace('app/src/main/AndroidManifest.xml',
        '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>\n',
        '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>\n'
        '    <uses-permission android:name="android.permission.READ_MEDIA_AUDIO"/>\n'
        '    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32"/>\n')

# --- Remove YouTube bootstrap from Application ---
write('app/src/main/java/com/music/spotui/MyApplication.kt', '''package com.music.spotui

import android.app.Application
import com.music.spotui.data.api.Api
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import timber.log.Timber

@HiltAndroidApp
class MyApplication : Application() {
    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    companion object {
        @JvmStatic
        lateinit var instance: MyApplication
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        if (BuildConfig.DEBUG && Timber.forest().isEmpty()) Timber.plant(Timber.DebugTree())
        com.metrolist.spotify.Spotify.logger = { level, msg ->
            android.util.Log.d("SpotifyREST", "[$level] $msg")
        }
        com.metrolist.spotify.SpotifyCanvas.setLogger { level, msg ->
            android.util.Log.d("SpotifyCanvas", "[$level] $msg")
        }

        // Warm Spotify metadata caches only. Audio resolution is exclusively Monochrome.
        val api = Api(this)
        appScope.launch { runCatching { api.getHomeFeed().collect {} } }
        appScope.launch { runCatching { api.getAlbums().collect {} } }
        appScope.launch { runCatching { api.getArtists().collect {} } }
    }
}
''')

# --- Spotify-only source preference ---
write('app/src/main/java/com/music/spotui/data/preferences/MusicSourcePref.kt', '''package com.music.spotui.data.preferences

import android.content.Context

enum class MusicSource(val label: String) {
    MONOCHROME("Monochrome"),
}

private const val PREF = "music_source"
private const val KEY_PRIMARY = "primary"

private fun prefs(context: Context) = context.getSharedPreferences(PREF, Context.MODE_PRIVATE)

fun getPrimaryMusicSource(context: Context): MusicSource = MusicSource.MONOCHROME

fun setPrimaryMusicSource(context: Context, source: MusicSource) {
    prefs(context).edit().putString(KEY_PRIMARY, MusicSource.MONOCHROME.name).apply()
}
''')

# --- Navigation: remove old provider onboarding/routes and keep LocalFiles ---
write('app/src/main/java/com/music/spotui/ui/navigation/Routes.kt', '''package com.music.spotui.ui.navigation

import androidx.annotation.DrawableRes
import com.music.spotui.R

sealed class Routes(@DrawableRes val icon: Int = 0, val label: String, val route: String) {
    object Home : Routes(R.drawable.ic_home_filled, "Home", "home")
    object Search : Routes(R.drawable.ic_search_big, "Search", "search")
    object Library : Routes(R.drawable.ic_library_big, "Library", "library")
    object Album : Routes(0, "Album", "album")
    object Player : Routes(0, "Player", "player")
    object Artist : Routes(0, "Artist", "artist")
    object ArtistReleases : Routes(0, "ArtistReleases", "artistreleases")
    object Playlist : Routes(0, "Playlist", "playlist")
    object Show : Routes(0, "Show", "show")
    object Queue : Routes(0, "Queue", "queue")
    object Liked : Routes(0, "Liked", "liked")
    object Downloads : Routes(0, "Downloads", "downloads")
    object Category : Routes(0, "Category", "category")
    object Login : Routes(0, "Login", "login")
    object Settings : Routes(0, "Settings", "settings")
    object History : Routes(0, "History", "history")
    object MusicSource : Routes(0, "MusicSource", "musicsource")
    object LocalFiles : Routes(0, "LocalFiles", "localfiles")
}

fun categoryRoute(genre: String, title: String): String =
    "${Routes.Category.route}/${android.net.Uri.encode(genre)}?title=${android.net.Uri.encode(title)}"

fun playlistRoute(id: String, name: String = ""): String =
    "${Routes.Playlist.route}/${android.net.Uri.encode(id)}?name=${android.net.Uri.encode(name)}"

fun showRoute(id: String, name: String = ""): String =
    "${Routes.Show.route}/${android.net.Uri.encode(id)}?name=${android.net.Uri.encode(name)}"

fun artistRoute(name: String, id: String = ""): String {
    val base = "${Routes.Artist.route}/${android.net.Uri.encode(name)}"
    return if (id.isBlank()) base else "$base?id=${android.net.Uri.encode(id)}"
}

fun albumRoute(name: String, artist: String = ""): String {
    val base = "${Routes.Album.route}/$name"
    return if (artist.isBlank()) base else "$base?artist=${android.net.Uri.encode(artist)}"
}
''')

# --- Simple Monochrome-backed playback engine ---
write('app/src/main/java/com/music/spotui/di/SongPlayer.kt', r'''package com.music.spotui.di

import android.content.Context
import android.net.Uri
import android.util.Log
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.MimeTypes
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.datasource.DefaultDataSource
import androidx.media3.datasource.DefaultHttpDataSource
import com.music.spotui.data.entity.SongsModel
import com.music.spotui.data.preferences.addDownload
import com.music.spotui.data.preferences.downloadedPathForQuery
import com.music.spotui.data.preferences.isDownloaded
import com.music.spotui.data.preferences.removeDownload
import com.music.spotui.data.preferences.getDownloadQuality
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ConcurrentHashMap

/**
 * Native player for Spotify metadata backed by Monochrome's official Hi-Fi API.
 * No other online playback provider is consulted.
 */
object SongPlayer {
    private const val TAG = "SongPlayer"
    private const val PREFIX = "spotify:track:"
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val cache = ConcurrentHashMap<String, String>()
    private val qualityCache = ConcurrentHashMap<String, String>()
    private var player: ExoPlayer? = null
    private var context: Context? = null
    private var currentRequest = ""
    private var metaTitle = ""
    private var metaArtist = ""
    private var metaCover = ""
    private var restoreQuery: String? = null
    private var restorePositionMs = 0L

    @Volatile var currentSource: String = "Monochrome"
        private set
    @Volatile var currentQuality: String = ""
        private set
    @Volatile var onStreamFailed: ((String) -> Unit)? = null
    @Volatile var onDownloadsChanged: (() -> Unit)? = null
    @Volatile var lastDownloadError: String? = null
    @Volatile var onPlayerSwapped: ((ExoPlayer) -> Unit)? = null

    private val downloading = ConcurrentHashMap.newKeySet<String>()
    private val progress = ConcurrentHashMap<String, Int>()
    private val downloadingSongs = ConcurrentHashMap<String, SongsModel>()

    val exoPlayer: ExoPlayer? get() = player
    val isPlaying: Boolean get() = player?.isPlaying == true
    val currentPosition: Long get() = player?.currentPosition ?: 0L
    val duration: Long get() = player?.duration?.takeIf { it > 0 } ?: 0L

    fun ensureCreated(ctx: Context): ExoPlayer {
        if (player == null) {
            context = ctx.applicationContext
            player = ExoPlayer.Builder(context!!).build().also { p ->
                p.addListener(object : Player.Listener {
                    override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                        val q = currentRequest
                        if (q.isNotBlank()) {
                            cache.remove(q)
                            onStreamFailed?.invoke(q)
                        }
                    }
                })
            }
        }
        return player!!
    }

    fun bindState(state: CurrentSongState) = Unit

    fun setNowPlayingMeta(title: String, artist: String, coverUri: String) {
        metaTitle = title; metaArtist = artist; metaCover = coverUri
    }

    fun buildSpotifyPlayQuery(spotifyTrackId: String, title: String, artist: String): String {
        val q = listOf(title, artist).filter { it.isNotBlank() }.joinToString(" ")
        return if (spotifyTrackId.isBlank()) q else "$PREFIX$spotifyTrackId|$q"
    }

    fun registerLossless(pairs: List<Pair<String, String>>) = Unit
    fun registerAlternativeKeys(pairs: List<Pair<String, String>>) = Unit
    fun registerExplicit(pairs: List<Pair<String, Boolean>>) = Unit
    fun registerDuration(pairs: List<Pair<String, Int>>) = Unit
    data class TrackMatchMetadata(val title: String, val artist: String, val album: String, val isrc: String = "")
    fun registerMetadata(pairs: List<Pair<String, TrackMatchMetadata>>) = Unit

    fun invalidateResolvedStream(song: String) {
        cache.remove(song); qualityCache.remove(song)
    }

    fun setRestorePoint(query: String, positionMs: Long) {
        restoreQuery = query; restorePositionMs = positionMs
    }

    fun playSong(song: String, ctx: Context) {
        val app = ctx.applicationContext
        context = app
        currentRequest = song
        val p = ensureCreated(app)
        p.pause(); p.clearMediaItems()

        downloadedPathForQuery(app, song)?.let { path ->
            currentSource = "Downloaded"
            currentQuality = path.substringAfterLast('.', "").uppercase()
            setMediaAndPlay(Uri.fromFile(File(path)).toString(), app)
            return
        }

        if (song.startsWith("content://") || song.startsWith("file://")) {
            currentSource = "Local"
            currentQuality = song.substringBefore('?').substringAfterLast('.', "").uppercase()
            setMediaAndPlay(song, app)
            return
        }

        scope.launch {
            val resolved = runCatching { MonochromeClient.resolveSpotifyQuery(song) }.getOrNull()
            if (currentRequest != song) return@launch
            if (resolved == null) {
                withContext(Dispatchers.Main) {
                    android.widget.Toast.makeText(app, "Monochrome couldn't find a playable stream", android.widget.Toast.LENGTH_SHORT).show()
                    onStreamFailed?.invoke(song)
                }
                return@launch
            }
            cache[song] = resolved.url
            qualityCache[song] = resolved.qualityLabel
            currentSource = "Monochrome"
            currentQuality = resolved.qualityLabel
            withContext(Dispatchers.Main) {
                if (currentRequest == song) {
                    setMediaAndPlay(resolved.url, app, resolved.isDash)
                }
            }
        }
    }

    private fun setMediaAndPlay(url: String, app: Context, dash: Boolean = false) {
        val p = ensureCreated(app)
        val metadata = MediaMetadata.Builder().setTitle(metaTitle).setArtist(metaArtist)
            .apply { if (metaCover.isNotBlank()) setArtworkUri(Uri.parse(metaCover)) }.build()
        val item = MediaItem.Builder().setUri(url)
            .setMediaMetadata(metadata)
            .apply { if (dash) setMimeType(MimeTypes.APPLICATION_MPD) }.build()
        p.setMediaItem(item)
        p.prepare()
        if (currentRequest == restoreQuery && restorePositionMs > 0) p.seekTo(restorePositionMs)
        restoreQuery = null; restorePositionMs = 0L
        p.playWhenReady = true
    }

    fun play() { player?.play() }
    fun pause() { player?.pause() }
    fun togglePlayPause() { if (isPlaying) pause() else play() }
    fun seekTo(positionMs: Long) { player?.seekTo(positionMs.coerceAtLeast(0)) }
    fun seekForward() { player?.seekForward() }
    fun seekBack() { player?.seekBack() }
    fun stop() { player?.stop() }

    fun prefetch(song: String, context: Context) {
        if (song.isBlank() || cache.containsKey(song)) return
        scope.launch {
            MonochromeClient.resolveSpotifyQuery(song)?.let { r ->
                cache[song] = r.url; qualityCache[song] = r.qualityLabel
            }
        }
    }

    fun prefetchList(songs: List<String>, context: Context, count: Int = 4) {
        songs.take(count).forEach { prefetch(it, context) }
    }

    fun webPlaybackActive(): Boolean = false

    fun isDownloading(query: String): Boolean = downloading.contains(query)
    fun downloadProgress(query: String): Int = progress[query] ?: -1
    fun downloadingSnapshot(): List<Pair<SongsModel, Int>> = downloadingSongs.entries.map { it.value to (progress[it.key] ?: 0) }

    fun allDownloaded(songs: List<SongsModel>, context: Context): Boolean =
        songs.isNotEmpty() && songs.all { isDownloaded(context, it.id.toString()) }

    fun downloadAll(songs: List<SongsModel>, context: Context) = songs.forEach { downloadSong(it, context) }

    fun downloadSong(song: SongsModel, ctx: Context, onComplete: (Boolean) -> Unit = {}) {
        val app = ctx.applicationContext
        if (song.url.isBlank() || isDownloaded(app, song.id.toString()) || !downloading.add(song.url)) return
        downloadingSongs[song.url] = song; progress[song.url] = 0; lastDownloadError = null
        onDownloadsChanged?.invoke()
        scope.launch {
            val ok = runCatching { downloadToFile(song, app) }.getOrDefault(false)
            downloading.remove(song.url); downloadingSongs.remove(song.url); progress.remove(song.url)
            withContext(Dispatchers.Main) { onDownloadsChanged?.invoke(); onComplete(ok) }
        }
    }

    private suspend fun downloadToFile(song: SongsModel, app: Context): Boolean {
        val resolved = MonochromeClient.resolveSpotifyQuery(song.url) ?: run { lastDownloadError = "Monochrome couldn't resolve this track"; return false }
        val dir = File(app.filesDir, "downloads").apply { mkdirs() }
        val ext = if (resolved.isDash) "flac" else "flac"
        val out = File(dir, "${song.id}.$ext")
        val tmp = File(dir, "${song.id}.part")
        return try {
            if (resolved.isDash) {
                if (!MonochromeClient.downloadDashToFlac(resolved.url, tmp, song.url, progress)) false
                else true
            } else {
                rangedDownload(resolved.url, tmp, song.url)
            }.also { ok ->
                if (ok) {
                    if (!tmp.renameTo(out)) return false
                    addDownload(app, song, out.absolutePath)
                } else tmp.delete()
            }
        } catch (e: Exception) {
            lastDownloadError = e.message ?: "Download failed"; tmp.delete(); false
        }
    }

    private fun rangedDownload(url: String, out: File, query: String): Boolean {
        val conn = (URL(url).openConnection() as HttpURLConnection).apply {
            connectTimeout = 15000; readTimeout = 30000; instanceFollowRedirects = true
            setRequestProperty("User-Agent", "Spotui/Monochrome Android")
        }
        return try {
            val total = conn.contentLengthLong
            if (conn.responseCode !in 200..299) return false
            conn.inputStream.use { input -> out.outputStream().buffered().use { output ->
                val buf = ByteArray(64 * 1024); var done = 0L
                while (true) {
                    val n = input.read(buf); if (n < 0) break
                    output.write(buf, 0, n); done += n
                    if (total > 0) progress[query] = ((done * 100) / total).toInt().coerceIn(0, 100)
                }
            }}
            progress[query] = 100; true
        } catch (e: Exception) { lastDownloadError = e.message ?: "Download failed"; false }
        finally { conn.disconnect() }
    }

    fun release() { player?.release(); player = null; currentRequest = "" }
}
''')

# --- Monochrome API client ---
write('app/src/main/java/com/music/spotui/di/MonochromeClient.kt', r'''package com.music.spotui.di

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.Base64
import java.util.concurrent.TimeUnit
import kotlin.math.abs

/**
 * Client for Monochrome's official Hi-Fi API layer. The web frontend is not used.
 * Search uses /search; playback uses /trackManifests and its signed TIDAL manifest.
 */
object MonochromeClient {
    private const val TAG = "MonochromeClient"
    private val instances = listOf(
        "https://api.monochrome.tf",
        "https://monochrome-api.samidy.com",
    )
    private val http = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .callTimeout(40, TimeUnit.SECONDS)
        .build()

    data class Resolved(val url: String, val qualityLabel: String, val isDash: Boolean)

    private data class Candidate(val id: String, val title: String, val artist: String, val duration: Int)

    suspend fun search(query: String, limit: Int = 10): List<Candidate> = withContext(Dispatchers.IO) {
        val out = mutableListOf<Candidate>()
        for (base in instances) {
            try {
                val url = "$base/search/".toHttpUrl().newBuilder()
                    .addQueryParameter("s", query)
                    .addQueryParameter("limit", limit.toString())
                    .build()
                val json = get(url.toString()) ?: continue
                val items = json.optJSONObject("data")?.optJSONArray("items") ?: JSONArray()
                for (i in 0 until items.length()) {
                    val o = items.optJSONObject(i) ?: continue
                    val artist = o.optJSONArray("artists")?.optJSONObject(0)?.optString("name")
                        ?: o.optJSONObject("artist")?.optString("name").orEmpty()
                    out += Candidate(o.optString("id"), o.optString("title"), artist, o.optInt("duration", 0))
                }
                if (out.isNotEmpty()) return@withContext out
            } catch (e: Exception) { Log.w(TAG, "search failed on $base: ${e.message}") }
        }
        out
    }

    suspend fun resolveSpotifyQuery(song: String): Resolved? = withContext(Dispatchers.IO) {
        if (song.startsWith("content://") || song.startsWith("file://")) return@withContext Resolved(song, "Local", false)
        val query = song.substringAfter('|', song.removePrefix("spotify:track:"))
        val expectedTitle = query.substringBeforeLast(' ').trim()
        val candidates = search(query, 12)
        val best = candidates.maxByOrNull { c ->
            val title = similarity(c.title, expectedTitle)
            val artist = similarity(c.artist, query.substringAfterLast(' '))
            title * 3 + artist + if (c.duration > 0) 0.1 else 0.0
        } ?: return@withContext null
        resolveTrack(best.id)
    }

    suspend fun resolveTrack(tidalId: String): Resolved? = withContext(Dispatchers.IO) {
        for (base in instances) {
            try {
                val u = "$base/trackManifests/".toHttpUrl().newBuilder()
                    .addQueryParameter("id", tidalId)
                    .addQueryParameter("quality", "LOSSLESS")
                    .addQueryParameter("adaptive", "false")
                    .addQueryParameter("formats", "FLAC")
                    .addQueryParameter("usage", "PLAYBACK")
                    .build()
                val lookup = get(u.toString()) ?: continue
                val uri = extractManifestUri(lookup) ?: continue
                val manifest = getText(uri) ?: continue
                if (manifest.contains("<MPD", true)) {
                    val duration = Regex("mediaPresentationDuration=\\\"PT(?:([0-9]+)H)?(?:([0-9]+)M)?([0-9.]+)S\\\"")
                        .find(manifest)?.let { m -> (m.groupValues[1].toDoubleOrNull() ?: 0.0) * 3600 + (m.groupValues[2].toDoubleOrNull() ?: 0.0) * 60 + (m.groupValues[3].toDoubleOrNull() ?: 0.0) }
                    if (duration != null && duration < 45) continue
                    return@withContext Resolved(uri, "FLAC 16-bit", true)
                }
                val flac = extractFlacUrl(manifest)
                if (flac != null) return@withContext Resolved(flac, "FLAC 16-bit", false)
            } catch (e: Exception) { Log.w(TAG, "resolve failed on $base: ${e.message}") }
        }
        null
    }

    private fun get(url: String): JSONObject? = runCatching {
        val req = Request.Builder().url(url).header("User-Agent", "Spotui/Monochrome Android").header("Accept", "application/json").build()
        http.newCall(req).execute().use { if (!it.isSuccessful) null else JSONObject(it.body?.string().orEmpty()) }
    }.getOrNull()

    private fun getText(url: String): String? = runCatching {
        val req = Request.Builder().url(url).header("User-Agent", "Spotui/Monochrome Android").build()
        http.newCall(req).execute().use { if (!it.isSuccessful) null else it.body?.string() }
    }.getOrNull()

    private fun extractManifestUri(root: JSONObject): String? {
        val data = root.optJSONObject("data")
        val nested = data?.optJSONObject("data") ?: data ?: root
        return nested.optJSONObject("attributes")?.optString("uri")?.takeIf { it.startsWith("http") }
    }

    private fun extractFlacUrl(text: String): String? {
        fun parse(raw: String): String? = runCatching {
            val o = JSONObject(raw)
            val urls = o.optJSONArray("urls") ?: return@runCatching null
            for (i in 0 until urls.length()) {
                val u = urls.optString(i)
                if (u.isNotBlank()) return@runCatching u
            }
            null
        }.getOrNull()
        parse(text)?.let { return it }
        val decoded = runCatching { String(Base64.getMimeDecoder().decode(text.trim())) }.getOrNull()
        return decoded?.let(::parse)
    }

    private fun similarity(a: String, b: String): Double {
        val na = normalize(a); val nb = normalize(b)
        if (na == nb) return 1.0
        if (na.isBlank() || nb.isBlank()) return 0.0
        val common = na.split(' ').intersect(nb.split(' ').toSet()).size.toDouble()
        return common / maxOf(na.split(' ').size, nb.split(' ').size, 1)
    }
    private fun normalize(s: String) = s.lowercase().replace(Regex("[^\\p{L}\\p{Nd} ]"), " ").replace(Regex("\\s+"), " ").trim()

    /** Download a DASH manifest returned by Monochrome into a normal FLAC file. */
    suspend fun downloadDashToFlac(manifestUrl: String, out: File, query: String, progress: java.util.concurrent.ConcurrentHashMap<String, Int>): Boolean = withContext(Dispatchers.IO) {
        try {
            val mpd = getText(manifestUrl) ?: return@withContext false
            val init = Regex("initialization=\\\"([^\\\"]+)\\\"").find(mpd)?.groupValues?.get(1) ?: return@withContext false
            val media = Regex("media=\\\"([^\\\"]+)\\\"").find(mpd)?.groupValues?.get(1) ?: return@withContext false
            val start = Regex("startNumber=\\\"(\\d+)\\\"").find(mpd)?.groupValues?.get(1)?.toIntOrNull() ?: 1
            val count = Regex("<S\\b[^>]*/?>").findAll(mpd).sumOf { 1 + (Regex("\\br=\\\"(\\d+)\\\"").find(it.value)?.groupValues?.get(1)?.toIntOrNull() ?: 0) }
            if (count <= 0) return@withContext false
            val initBytes = getBytes(resolveUrl(manifestUrl, init)) ?: return@withContext false
            val streamInfo = findStreamInfo(initBytes) ?: return@withContext false
            out.outputStream().buffered().use { os ->
                os.write(byteArrayOf(0x66, 0x4c, 0x61, 0x43)); os.write(0x80)
                os.write((streamInfo.size ushr 16) and 0xff); os.write((streamInfo.size ushr 8) and 0xff); os.write(streamInfo.size and 0xff); os.write(streamInfo)
                for (n in start until start + count) {
                    val bytes = getBytes(resolveUrl(manifestUrl, media.replace("$" + "Number$", n.toString()))) ?: return@withContext false
                    writeMdat(bytes, os)
                    progress[query] = (((n - start + 1) * 100) / count).coerceIn(0, 100)
                }
            }
            progress[query] = 100
            true
        } catch (e: Exception) { Log.w(TAG, "DASH download failed: ${e.message}"); false }
    }

    private fun resolveUrl(base: String, value: String): String {
        if (value.startsWith("http")) return value
        val b = java.net.URI(base); return b.resolve(value).toString()
    }
    private fun getBytes(url: String): ByteArray? = runCatching {
        val req = Request.Builder().url(url).header("User-Agent", "Spotui/Monochrome Android").build()
        http.newCall(req).execute().use { if (!it.isSuccessful) null else it.body?.bytes() }
    }.getOrNull()
    private fun findStreamInfo(bytes: ByteArray): ByteArray? {
        val tag = byteArrayOf(0x64, 0x66, 0x4c, 0x61)
        for (i in 0..bytes.size - tag.size - 8) if (tag.indices.all { bytes[i + it] == tag[it] }) {
            val len = ((bytes[i + 9].toInt() and 255) shl 16) or ((bytes[i + 10].toInt() and 255) shl 8) or (bytes[i + 11].toInt() and 255)
            if (len > 0 && i + 12 + len <= bytes.size) return bytes.copyOfRange(i + 12, i + 12 + len)
        }
        return null
    }
    private fun writeMdat(bytes: ByteArray, out: OutputStream) {
        var i = 0
        while (i + 8 <= bytes.size) {
            var size = ((bytes[i].toLong() and 255) shl 24) or ((bytes[i+1].toLong() and 255) shl 16) or ((bytes[i+2].toLong() and 255) shl 8) or (bytes[i+3].toLong() and 255)
            var header = 8
            if (size == 1L) { if (i + 16 > bytes.size) return; size = (0..7).fold(0L) { a, n -> (a shl 8) or (bytes[i+8+n].toLong() and 255) }; header = 16 }
            if (size < header || i + size > bytes.size) return
            if (bytes.copyOfRange(i + 4, i + 8).contentEquals(byteArrayOf(0x6d,0x64,0x61,0x74))) out.write(bytes, i + header, (size - header).toInt())
            i += size.toInt()
        }
    }
}
''')

# --- Navigation host: same app, no provider login routes; local files remains ---
nav = '''package com.music.spotui.ui.navigation

import android.os.Build
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.music.spotui.data.api.SpotifySession
import com.music.spotui.ui.screens.*
import com.music.spotui.ui.viewmodel.PlayerViewModel

@RequiresApi(Build.VERSION_CODES.S)
@Composable
fun MyNavHost(navHostController: NavHostController, bottomBarState: MutableState<Boolean>, bottomBarPlayerState: MutableState<Boolean>) {
    val vm: PlayerViewModel = hiltViewModel()
    val playerState by vm.currentSongTitle
    val context = LocalContext.current
    val start = if (SpotifySession.spDc(context).isBlank()) Routes.Login.route else Routes.Home.route
    LaunchedEffect(Unit) {
        if (vm.currentSongTitle.value.isBlank()) com.music.spotui.data.preferences.loadLastPlayback(context)?.let { (song, pos) ->
            vm.updateQueue(listOf(song)); vm.updateSongState(song.coverUri, song.title, song.singer, false, song.id, 0, song.album); com.music.spotui.di.SongPlayer.setRestorePoint(song.url, pos)
        }
    }
    NavHost(navHostController, start, enterTransition={ fadeIn(tween(150)) }, exitTransition={ fadeOut(tween(150)) }, popEnterTransition={ fadeIn(tween(150)) }, popExitTransition={ fadeOut(tween(150)) }) {
        composable(Routes.Login.route) { LaunchedEffect(Unit) { bottomBarState.value=false; bottomBarPlayerState.value=false }; SpotifyLoginScreen(navHostController) }
        composable(Routes.Home.route) { LaunchedEffect(playerState) { bottomBarState.value=true; bottomBarPlayerState.value=playerState.isNotBlank() }; HomeScreen(navHostController) }
        composable(Routes.Search.route) { LaunchedEffect(playerState) { bottomBarState.value=true; bottomBarPlayerState.value=playerState.isNotBlank() }; SearchScreen(navHostController) }
        composable(Routes.Library.route) { LaunchedEffect(playerState) { bottomBarState.value=true; bottomBarPlayerState.value=playerState.isNotBlank() }; LibraryScreen(navHostController) }
        composable(Routes.Player.route) { LaunchedEffect(playerState) { bottomBarState.value=false; bottomBarPlayerState.value=playerState.isNotBlank() }; PlayerScreen(navHostController) }
        composable(Routes.Queue.route) { LaunchedEffect(Unit) { bottomBarState.value=false; bottomBarPlayerState.value=false }; QueueScreen(navHostController) }
        composable(Routes.Liked.route) { LaunchedEffect(playerState) { bottomBarState.value=true; bottomBarPlayerState.value=playerState.isNotBlank() }; LikedSongsScreen(navHostController) }
        composable(Routes.Downloads.route) { LaunchedEffect(playerState) { bottomBarState.value=true; bottomBarPlayerState.value=playerState.isNotBlank() }; DownloadsScreen(navHostController) }
        composable(Routes.Settings.route) { LaunchedEffect(playerState) { bottomBarState.value=true; bottomBarPlayerState.value=playerState.isNotBlank() }; SettingsScreen(navHostController) }
        composable(Routes.History.route) { LaunchedEffect(playerState) { bottomBarState.value=true; bottomBarPlayerState.value=playerState.isNotBlank() }; HistoryScreen(navHostController) }
        composable(Routes.MusicSource.route) { LaunchedEffect(Unit) { bottomBarState.value=false; bottomBarPlayerState.value=false }; MusicSourceScreen(navHostController) }
        composable(Routes.LocalFiles.route) { LaunchedEffect(playerState) { bottomBarState.value=true; bottomBarPlayerState.value=playerState.isNotBlank() }; LocalFilesScreen(navHostController) }
        composable("${Routes.Category.route}/{genre}?title={title}", arguments=listOf(navArgument("title"){defaultValue=""})) { e -> CategoryScreen(navHostController, e.arguments?.getString("genre").orEmpty(), e.arguments?.getString("title").orEmpty()) }
        composable("${Routes.Album.route}/{uString}?artist={artist}", arguments=listOf(navArgument("artist"){defaultValue=""})) { e -> e.arguments?.getString("uString")?.let { AlbumScreen(navHostController,it,e.arguments?.getString("artist").orEmpty()) } }
        composable("${Routes.Playlist.route}/{pId}?name={name}", arguments=listOf(navArgument("name"){defaultValue=""})) { e -> e.arguments?.getString("pId")?.let { PlaylistScreen(navHostController,it,e.arguments?.getString("name").orEmpty()) } }
        composable("${Routes.Show.route}/{sId}?name={name}", arguments=listOf(navArgument("name"){defaultValue=""})) { e -> e.arguments?.getString("sId")?.let { ShowScreen(navHostController,it,e.arguments?.getString("name").orEmpty()) } }
        composable("${Routes.ArtistReleases.route}/{aString}") { e -> e.arguments?.getString("aString")?.let { ArtistReleasesScreen(navHostController,it) } }
        composable("${Routes.Artist.route}/{aString}?id={artistId}", arguments=listOf(navArgument("artistId"){defaultValue=""})) { e -> e.arguments?.getString("aString")?.let { ArtistScreen(navHostController,it,e.arguments?.getString("artistId").orEmpty()) } }
    }
}
'''
write('app/src/main/java/com/music/spotui/ui/navigation/MyNavHost.kt', nav)

# --- Onboarding source screen becomes informational Monochrome screen ---
write('app/src/main/java/com/music/spotui/ui/screens/MusicSourceScreen.kt', '''package com.music.spotui.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.music.spotui.data.preferences.MusicSource
import com.music.spotui.data.preferences.setPrimaryMusicSource
import com.music.spotui.ui.navigation.Routes

@Composable
fun MusicSourceScreen(navController: NavController) {
    val context = androidx.compose.ui.platform.LocalContext.current
    setPrimaryMusicSource(context, MusicSource.MONOCHROME)
    Box(Modifier.fillMaxSize().background(Color.Black), contentAlignment=Alignment.Center) {
        Column(Modifier.padding(24.dp), horizontalAlignment=Alignment.CenterHorizontally) {
            Text("Monochrome", color=Color.White, fontSize=28.sp)
            Spacer(Modifier.height(12.dp))
            Text("Spotify remains the metadata and library provider. Monochrome is the sole online audio backend.", color=Color.LightGray, fontSize=14.sp)
            Spacer(Modifier.height(24.dp))
            Text("Continue", color=Color.White, fontSize=16.sp, modifier=Modifier.clickable { navController.navigate(Routes.Home.route) { popUpTo(Routes.MusicSource.route) { inclusive=true } } }.padding(16.dp))
        }
    }
}
''')

# --- MainActivity: remove hidden Spotify web player ---
main = (ROOT/'app/src/main/java/com/music/spotui/MainActivity.kt').read_text(encoding='utf-8')
main = re.sub(r'\n\s*// Experimental Spotify web-player engine:.*?SpotifyWebPlayer\.attach\(this\)\n\s*\}', '\n    }', main, flags=re.S)
(ROOT/'app/src/main/java/com/music/spotui/MainActivity.kt').write_text(main, encoding='utf-8')

# --- PlaybackService: remove web engine and use ExoPlayer only ---
ps = (ROOT/'app/src/main/java/com/music/spotui/ui/notification/PlaybackService.kt').read_text(encoding='utf-8')
ps = ps.replace('import com.music.spotui.di.SpotifyWebPlayer\n', '')
ps = re.sub(r'\n\s*private var webPlayer: WebMediaPlayer\? = null\n\s*private var showingWeb = false\n', '\n', ps)
ps = re.sub(r'\n\s*webPlayer = WebMediaPlayer\(mainLooper, currentSongState\) \{ forward -> advance\(forward\) \}\n', '\n', ps)
ps = re.sub(r'\n\s*SongPlayer\.onPlayerSwapped = \{ newPlayer ->\n\s*if \(!showingWeb\) mediaSession\?\.player = wrap\(newPlayer\)\n\s*\}\n', '\n', ps)
ps = re.sub(r'\n\s*// As the hidden web player streams.*?\n\s*\}\n\s*\}\n', '\n', ps, flags=re.S)
ps = ps.replace('''        val wantWeb = SongPlayer.webPlaybackActive()\n        if (wantWeb == showingWeb) return\n        showingWeb = wantWeb\n        val session = mediaSession ?: return\n        session.player = if (wantWeb) {\n            webPlayer ?: return\n        } else {\n            wrap(SongPlayer.exoPlayer ?: return)\n        }''', '''        mediaSession?.player = wrap(SongPlayer.exoPlayer ?: return)''')
ps = re.sub(r'\n\s*/\*\* Point the media session at whichever engine is currently producing audio\. \*/\n\s*private fun syncSessionPlayer\(\) \{.*?\n\s*\}\n', '', ps, flags=re.S)
# Remove any leftover showingWeb/webPlayer references defensively.
ps = re.sub(r'\n\s*if \(showingWeb\) \{[^}]*\}', '', ps, flags=re.S)
ps = ps.replace('SongPlayer.onPlayerSwapped = { newPlayer -> mediaSession?.player = wrap(newPlayer) }', '')
(ROOT/'app/src/main/java/com/music/spotui/ui/notification/PlaybackService.kt').write_text(ps, encoding='utf-8')

# --- Settings: keep quality/crossfade/account, remove all provider UI ---
write('app/src/main/java/com/music/spotui/ui/screens/SettingsScreen.kt', '''package com.music.spotui.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.music.spotui.data.api.Api
import com.music.spotui.data.api.SpotifySession
import com.music.spotui.data.preferences.*
import com.music.spotui.ui.theme.AppBackground
import com.music.spotui.ui.theme.AppPalette

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(navController: NavController) {
    val context = androidx.compose.ui.platform.LocalContext.current
    var wifiQ by remember { mutableStateOf(getWifiQuality(context)) }
    var cellQ by remember { mutableStateOf(getCellularQuality(context)) }
    var dlQ by remember { mutableStateOf(getDownloadQuality(context)) }
    var crossfade by remember { mutableStateOf(getCrossfadeMs(context).toFloat()) }
    Scaffold(containerColor=AppBackground, topBar={ CenterAlignedTopAppBar(title={Text("Settings",color=Color.White,fontWeight=FontWeight.Bold)}, navigationIcon={Icon(Icons.AutoMirrored.Filled.ArrowBack,"Back",tint=Color.White,modifier=Modifier.clickable{navController.popBackStack()})}, colors=TopAppBarDefaults.centerAlignedTopAppBarColors(containerColor=AppBackground)) }) { pad ->
        Column(Modifier.fillMaxSize().padding(pad).verticalScroll(rememberScrollState()).padding(16.dp)) {
            SectionTitle("Playback backend")
            Text("Monochrome", color=Color.White, fontSize=18.sp, fontWeight=FontWeight.Bold)
            Text("Sole online audio source. Spotui uses Monochrome's Hi-Fi API directly; the web frontend is not embedded.", color=Color.LightGray, fontSize=13.sp, modifier=Modifier.padding(top=4.dp))
            Spacer(Modifier.height(18.dp))
            SectionTitle("Audio quality")
            QualityPicker("Streaming over Wi-Fi", wifiQ) { wifiQ=it; setWifiQuality(context,it) }
            QualityPicker("Streaming over cellular", cellQ) { cellQ=it; setCellularQuality(context,it) }
            QualityPicker("Download quality", dlQ) { dlQ=it; setDownloadQuality(context,it) }
            Spacer(Modifier.height(12.dp)); SectionTitle("Crossfade")
            Text(if(crossfade<=0) "Off" else "${(crossfade/1000).toInt()}s",color=Color.White)
            Slider(value=crossfade,onValueChange={crossfade=it},onValueChangeFinished={setCrossfadeMs(context,crossfade.toInt())},valueRange=0f..CROSSFADE_MAX_MS.toFloat(),steps=(CROSSFADE_MAX_MS/1000)-1)
            Spacer(Modifier.height(12.dp)); SectionTitle("Local music")
            Text("Search and play audio indexed by Android MediaStore from Local files.",color=Color.LightGray,fontSize=13.sp)
            Text("Open Local files",color=AppPalette,fontWeight=FontWeight.Bold,modifier=Modifier.clickable{navController.navigate(Routes.LocalFiles.route)}.padding(vertical=12.dp))
            Spacer(Modifier.height(12.dp)); SectionTitle("Account")
            Text("Log out",color=Color(0xFFE57373),fontSize=16.sp,fontWeight=FontWeight.SemiBold,modifier=Modifier.fillMaxWidth().clickable{SpotifySession.setSpDc(context,"");Api.HomeCache.clear();navController.navigate(Routes.Login.route){popUpTo(0){inclusive=true}}}.padding(vertical=14.dp))
        }
    }
}

@Composable private fun SectionTitle(text:String){Text(text,color=AppPalette,fontSize=13.sp,fontWeight=FontWeight.Bold,modifier=Modifier.padding(top=16.dp,bottom=6.dp))}
@Composable private fun QualityPicker(title:String,selected:StreamQuality,onSelect:(StreamQuality)->Unit){Column(Modifier.padding(vertical=6.dp)){Text(title,color=Color.White,fontWeight=FontWeight.SemiBold);StreamQuality.entries.forEach{q->Row(Modifier.fillMaxWidth().clickable{onSelect(q)}.background(if(q==selected)Color(0xFF1A1A20) else Color.Transparent,RoundedCornerShape(10.dp)).padding(12.dp),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text(q.label,color=Color.White);Text(q.detail,color=Color.LightGray,fontSize=12.sp)};if(q==selected)Icon(Icons.Default.Check,"Selected",tint=AppPalette)}}}}
''')

# --- Local MediaStore index/search screen ---
write('app/src/main/java/com/music/spotui/data/local/MediaStoreLocalMusic.kt', '''package com.music.spotui.data.local

import android.content.Context
import android.provider.MediaStore
import com.music.spotui.data.entity.SongsModel

object MediaStoreLocalMusic {
    fun search(context: Context, query: String): List<SongsModel> {
        val resolver = context.contentResolver
        val projection = arrayOf(MediaStore.Audio.Media._ID, MediaStore.Audio.Media.TITLE, MediaStore.Audio.Media.ARTIST, MediaStore.Audio.Media.ALBUM, MediaStore.Audio.Media.DURATION, MediaStore.Audio.Media.ALBUM_ID)
        val selection = buildString {
            append("${MediaStore.Audio.Media.IS_MUSIC} != 0")
            if (query.isNotBlank()) append(" AND (${MediaStore.Audio.Media.TITLE} LIKE ? OR ${MediaStore.Audio.Media.ARTIST} LIKE ? OR ${MediaStore.Audio.Media.ALBUM} LIKE ?)")
        }
        val args = if (query.isBlank()) null else arrayOf("%$query%","%$query%","%$query%")
        val sort = "${MediaStore.Audio.Media.TITLE} COLLATE NOCASE ASC"
        return buildList {
            resolver.query(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, projection, selection, args, sort)?.use { c ->
                val idCol=c.getColumnIndexOrThrow(MediaStore.Audio.Media._ID); val titleCol=c.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE); val artistCol=c.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST); val albumCol=c.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM); val durCol=c.getColumnIndexOrThrow(MediaStore.Audio.Media.DURATION); val albumIdCol=c.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM_ID)
                while(c.moveToNext()) {
                    val id=c.getLong(idCol); val uri=android.content.ContentUris.withAppendedId(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,id)
                    val albumId=c.getLong(albumIdCol); val cover=if(albumId>0) "content://media/external/audio/albumart/$albumId" else ""
                    add(SongsModel(id.toInt(),c.getString(titleCol).orEmpty().ifBlank{"Unknown title"},c.getString(albumCol).orEmpty(),c.getString(artistCol).orEmpty().ifBlank{"Unknown artist"},cover,uri.toString(),"",false,c.getLong(durCol).toInt()))
                }
            }
        }
    }
}
''')

# Replace local screen with MediaStore search + existing imported library.
write('app/src/main/java/com/music/spotui/ui/screens/LocalFilesScreen.kt', '''package com.music.spotui.ui.screens

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.music.spotui.data.local.LocalImport
import com.music.spotui.data.local.MediaStoreLocalMusic
import com.music.spotui.data.preferences.*
import com.music.spotui.di.SongPlayer
import com.music.spotui.ui.theme.AppBackground
import com.music.spotui.ui.theme.AppPalette
import com.music.spotui.ui.viewmodel.PlayerViewModel
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable fun LocalFilesScreen(navController: NavController) {
    val context=LocalContext.current; val vm:PlayerViewModel=hiltViewModel(); var query by remember{mutableStateOf("")}; var results by remember{mutableStateOf(emptyList<com.music.spotui.data.entity.SongsModel>())}; var imported by remember{mutableStateOf(getLocalSongs(context))}
    fun refresh(){results=MediaStoreLocalMusic.search(context,query); imported=getLocalSongs(context)}
    val permission=rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()){if(it)refresh()}
    LaunchedEffect(Unit){val p=if(Build.VERSION.SDK_INT>=33)Manifest.permission.READ_MEDIA_AUDIO else Manifest.permission.READ_EXTERNAL_STORAGE;if(androidx.core.content.ContextCompat.checkSelfPermission(context,p)==android.content.pm.PackageManager.PERMISSION_GRANTED)refresh() else permission.launch(p)}
    Scaffold(containerColor=AppBackground,topBar={TopAppBar(title={Text("Local music",color=Color.White,fontWeight=FontWeight.Bold)},navigationIcon={Icon(Icons.AutoMirrored.Filled.ArrowBack,"Back",tint=Color.White,modifier=Modifier.clickable{navController.navigateUp()})},colors=TopAppBarDefaults.topAppBarColors(containerColor=AppBackground))}){pad->
        Column(Modifier.fillMaxSize().padding(pad)){
            OutlinedTextField(value=query,onValueChange={query=it;results=MediaStoreLocalMusic.search(context,it)},modifier=Modifier.fillMaxWidth().padding(16.dp),singleLine=true,label={Text("Search local music")})
            Row(Modifier.padding(horizontal=16.dp),horizontalArrangement=Arrangement.spacedBy(8.dp)){Button(onClick={refresh()}){Text("Refresh")};Text("MediaStore",color=AppPalette,modifier=Modifier.align(Alignment.CenterVertically))}
            LazyColumn(contentPadding=PaddingValues(bottom=120.dp)){
                if(query.isBlank() && imported.isNotEmpty()){item{Text("Imported local library",color=Color.White,fontSize=18.sp,fontWeight=FontWeight.Bold,modifier=Modifier.padding(16.dp))};items(imported.size){i->LocalRow(imported[i],i,imported,vm,context)}}
                item{Text(if(query.isBlank())"Device music" else "Device results",color=Color.White,fontSize=18.sp,fontWeight=FontWeight.Bold,modifier=Modifier.padding(16.dp))}
                items(results.size){i->LocalRow(results[i],i,results,vm,context)}
            }
        }
    }
}

@Composable private fun LocalRow(song:com.music.spotui.data.entity.SongsModel,index:Int,list:List<com.music.spotui.data.entity.SongsModel>,vm:PlayerViewModel,context:android.content.Context){Row(Modifier.fillMaxWidth().clickable{vm.updateQueue(list);vm.updateSongState(song.coverUri,song.title,song.singer,true,song.id,index,song.album);SongPlayer.playSong(song.url,context)}.padding(16.dp,10.dp),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text(song.title,color=Color.White,maxLines=1);Text("${song.singer}${if(song.album.isNotBlank())" • ${song.album}" else ""}",color=Color.Gray,fontSize=12.sp,maxLines=1)}Text("LOCAL",color=AppPalette,fontSize=10.sp,fontWeight=FontWeight.Bold)}}
''')

# Remove the obsolete source-picker route dependency from app startup: always Monochrome.
# The route remains only as a compatibility informational screen.

# Cleanup temporary tool files after migration has been applied.
remove('tools/migrate_monochrome.py')
remove('.github/workflows/migrate-monochrome.yml')

print('Monochrome migration applied')
''