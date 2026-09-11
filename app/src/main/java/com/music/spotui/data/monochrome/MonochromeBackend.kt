package com.music.spotui.data.monochrome

import com.music.spotui.data.entity.SongsModel
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import java.net.URLEncoder

class MonochromeBackend(
    private val baseUrl: String = MonochromeConfig.BASE_URL,
    private val token: String = MonochromeConfig.API_TOKEN,
    private val client: OkHttpClient = OkHttpClient(),
) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun resolve(song: SongsModel): String? = runCatching {
        val query = "${baseUrl.trimEnd('/')}/api/v2/track/?track=${enc(song.title)}&artist=${enc(song.singer)}&album=${enc(song.album)}&intent=stream"
        val request = Request.Builder().url(query).apply {
            if (token.isNotBlank()) header("Authorization", "Bearer $token")
        }.build()
        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) return null
            val body = response.body?.string() ?: return null
            json.decodeFromString<PlaybackResponse>(body).playback.firstOrNull {
                it.url.isNotBlank() && (it.kind == "audio" || it.kind == "manifest")
            }?.url
        }
    }.getOrNull()

    private fun enc(value: String) = URLEncoder.encode(value, Charsets.UTF_8.name())
}

@Serializable
data class PlaybackResponse(val playback: List<PlaybackResource> = emptyList())

@Serializable
data class PlaybackResource(
    val url: String = "",
    val kind: String = "",
    val delivery: String = "",
)
