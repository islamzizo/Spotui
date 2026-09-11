package com.music.spotui.data.preferences

import android.content.Context

enum class MusicSource(val label: String) { MONOCHROME("Monochrome") }

private const val PREF = "music_source"
private const val KEY_PRIMARY = "primary"

fun getPrimaryMusicSource(context: Context): MusicSource = MusicSource.MONOCHROME
fun setPrimaryMusicSource(context: Context, source: MusicSource) {
    context.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putString(KEY_PRIMARY, MusicSource.MONOCHROME.name).apply()
}
