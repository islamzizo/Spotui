package com.music.spotui.data.monochrome

import com.music.spotui.data.entity.SongsModel

class MonochromeRepository(private val client: MonochromeClient = MonochromeClient()) {
    suspend fun resolve(song: SongsModel): MonochromePlayback? = runCatching {
        client.resolveTrack(
            track = song.title,
            artist = song.singer,
            album = song.album,
            durationMs = song.durationMs.toLong(),
        )
    }.getOrNull()
}
