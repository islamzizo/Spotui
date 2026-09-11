package com.music.spotui.data.local

import android.content.ContentUris
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.provider.MediaStore
import androidx.core.content.ContextCompat
import com.music.spotui.data.entity.SongsModel

object MediaStoreLocalMusic {
    fun hasReadPermission(context: Context): Boolean =
        if (Build.VERSION.SDK_INT >= 33) {
            ContextCompat.checkSelfPermission(context, "android.permission.READ_MEDIA_AUDIO") == PackageManager.PERMISSION_GRANTED
        } else {
            ContextCompat.checkSelfPermission(context, "android.permission.READ_EXTERNAL_STORAGE") == PackageManager.PERMISSION_GRANTED
        }

    fun search(context: Context, query: String): List<SongsModel> {
        if (!hasReadPermission(context)) return emptyList()
        val projection = arrayOf(
            MediaStore.Audio.Media._ID, MediaStore.Audio.Media.TITLE,
            MediaStore.Audio.Media.ARTIST, MediaStore.Audio.Media.ALBUM,
            MediaStore.Audio.Media.DURATION, MediaStore.Audio.Media.ALBUM_ID,
        )
        val selection = buildString {
            append("${MediaStore.Audio.Media.IS_MUSIC} != 0")
            if (query.isNotBlank()) append(" AND (${MediaStore.Audio.Media.TITLE} LIKE ? OR ${MediaStore.Audio.Media.ARTIST} LIKE ? OR ${MediaStore.Audio.Media.ALBUM} LIKE ?)")
        }
        val args = if (query.isBlank()) null else arrayOf("%$query%", "%$query%", "%$query%")
        return buildList {
            context.contentResolver.query(
                MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, projection, selection, args,
                "${MediaStore.Audio.Media.TITLE} COLLATE NOCASE ASC",
            )?.use { cursor ->
                val id = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
                val title = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)
                val artist = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST)
                val album = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM)
                val duration = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.DURATION)
                val albumId = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM_ID)
                while (cursor.moveToNext()) {
                    val mediaId = cursor.getLong(id)
                    val uri = ContentUris.withAppendedId(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, mediaId)
                    val aid = cursor.getLong(albumId)
                    val cover = if (aid > 0) "content://media/external/audio/albumart/$aid" else ""
                    add(SongsModel(mediaId.toInt(), cursor.getString(title).orEmpty().ifBlank { "Unknown title" }, cursor.getString(album).orEmpty(), cursor.getString(artist).orEmpty().ifBlank { "Unknown artist" }, cover, uri.toString(), "", false, cursor.getLong(duration).toInt()))
                }
            }
        }
    }
}
