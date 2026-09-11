package com.music.spotui.data.monochrome

import com.music.spotui.data.entity.SongsModel

class MonochromeRepository(
    private val client: MonochromeClient = MonochromeClient(),
) {
    suspend fun resolve(
        song: SongsModel,
        quality: String = "LOSSLESS",
        intent: String = "stream",
    ): MonochromePlayback? = runCatching {
        client.resolveTrack(
            track = song.title,
            artist = song.singer,
            album = song.album,
            durationMs = song.durationMs.toLong(),
            quality = quality,
            intent = intent,
        )
    }.getOrNull()
}
