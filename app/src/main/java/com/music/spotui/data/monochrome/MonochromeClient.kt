package com.music.spotui.data.monochrome

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException

/** Native client for Monochrome Unified Playback. */
class MonochromeClient(
    private val baseUrl: String = MonochromeConfig.BASE_URL,
    private val apiToken: String = MonochromeConfig.API_TOKEN,
    private val httpClient: OkHttpClient = OkHttpClient(),
) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun resolveTrack(
        track: String,
        artist: String,
        album: String = "",
        isrc: String = "",
        durationMs: Long = 0L,
        quality: String = "high",
    ): MonochromePlayback? {
        val url = buildString {
            append(baseUrl.trimEnd('/')); append("/api/v2/track/")
            append("?track=").append(track.urlEncode())
            append("&artist=").append(artist.urlEncode())
            if (album.isNotBlank()) append("&album=").append(album.urlEncode())
            if (isrc.isNotBlank()) append("&isrc=").append(isrc.urlEncode())
            if (durationMs > 0) append("&duration=").append(durationMs / 1000L)
            append("&intent=stream&quality=").append(quality.urlEncode())
        }
        val request = Request.Builder().url(url).apply {
            if (apiToken.isNotBlank()) header("Authorization", "Bearer $apiToken")
        }.get().build()
        val body = httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Monochrome HTTP ${response.code}")
            response.body?.string() ?: return null
        }
        return json.decodeFromString<MonochromeResponse>(body).playback.firstOrNull {
            it.url.isNotBlank() && (it.kind == "audio" || it.kind == "manifest")
        }
    }
}

@Serializable
data class MonochromeResponse(val playback: List<MonochromePlayback> = emptyList())

@Serializable
data class MonochromePlayback(
    val url: String = "",
    val kind: String = "",
    val delivery: String = "",
    val codec: String? = null,
    val quality: String? = null,
)

private fun String.urlEncode(): String = java.net.URLEncoder.encode(this, Charsets.UTF_8.name())
