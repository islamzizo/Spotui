package com.music.spotui.data.monochrome

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request

/** Native client for Monochrome Unified Playback. */
class MonochromeClient2(
    private val baseUrl: String = MonochromeConfig.BASE_URL,
    private val apiToken: String = MonochromeConfig.API_TOKEN,
    private val httpClient: OkHttpClient = OkHttpClient(),
) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun resolveTrack(track: String, artist: String, album: String = ""): MonochromePlayback? {
        val url = "${baseUrl.trimEnd('/')}/api/v2/track/?track=${track.urlEncode()}&artist=${artist.urlEncode()}&album=${album.urlEncode()}&intent=stream"
        val request = Request.Builder().url(url).apply {
            if (apiToken.isNotBlank()) header("Authorization", "Bearer $apiToken")
        }.build()
        val body = httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) return null
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
)

private fun String.urlEncode(): String = java.net.URLEncoder.encode(this, Charsets.UTF_8.name())
