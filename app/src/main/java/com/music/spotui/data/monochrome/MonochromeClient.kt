package com.music.spotui.data.monochrome

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException
import java.util.concurrent.TimeUnit

/** Native client for Monochrome's Unified Playback API. */
class MonochromeClient(
    private val baseUrl: String = MonochromeConfig.BASE_URL,
    private val httpClient: OkHttpClient = sharedHttpClient,
) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun resolveTrack(
        track: String,
        artist: String,
        album: String = "",
        isrc: String = "",
        durationMs: Long = 0L,
        quality: String = "LOSSLESS",
        intent: String = "stream",
    ): MonochromePlayback? {
        val url = buildString {
            append(baseUrl.trimEnd('/'))
            append("/api/v2/track/?track=").append(track.urlEncode())
            if (artist.isNotBlank()) append("&artist=").append(artist.urlEncode())
            if (album.isNotBlank()) append("&album=").append(album.urlEncode())
            if (isrc.isNotBlank()) append("&isrc=").append(isrc.urlEncode())
            if (durationMs > 0) append("&duration=").append(durationMs / 1000L)
            append("&intent=").append(intent.urlEncode())
            append("&quality=").append(quality.urlEncode())
        }

        val request = Request.Builder()
            .url(url)
            .header("Accept", "application/json")
            .get()
            .build()

        val response = httpClient.newCall(request).execute()
        response.use {
            if (!it.isSuccessful) {
                throw IOException("Monochrome HTTP ${it.code}")
            }
            val body = it.body?.string().orEmpty()
            if (body.isBlank()) return null
            return json.decodeFromString<MonochromeResponse>(body).playback.firstOrNull {
                it.url.isNotBlank() && (it.kind == "audio" || it.kind == "manifest")
            }
        }
    }

    companion object {
        private val sharedHttpClient = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .callTimeout(35, TimeUnit.SECONDS)
            .build()
    }
}

@Serializable
data class MonochromeResponse(
    val playback: List<MonochromePlayback> = emptyList(),
)

@Serializable
data class MonochromePlayback(
    val url: String = "",
    val kind: String = "",
    val delivery: String = "",
    val codec: String? = null,
    val quality: String? = null,
    val mimeType: String? = null,
    val mime_type: String? = null,
)

private fun String.urlEncode(): String =
    java.net.URLEncoder.encode(this, Charsets.UTF_8.name())
