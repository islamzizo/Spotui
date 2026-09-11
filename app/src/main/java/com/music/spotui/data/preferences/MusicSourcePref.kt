package com.music.spotui.data.preferences

import android.content.Context

/** Online playback backend. Spotify remains the metadata/account provider. */
enum class MusicSource(val label: String) {
    MONOCHROME("Monochrome"),
}

private const val PREF = "music_source"
private const val KEY_PRIMARY = "primary"

private fun sourcePrefs(context: Context) =
    context.getSharedPreferences(PREF, Context.MODE_PRIVATE)

fun getPrimaryMusicSource(context: Context): MusicSource =
    MusicSource.MONOCHROME

fun setPrimaryMusicSource(context: Context, source: MusicSource) {
    sourcePrefs(context).edit().putString(KEY_PRIMARY, MusicSource.MONOCHROME.name).apply()
}
