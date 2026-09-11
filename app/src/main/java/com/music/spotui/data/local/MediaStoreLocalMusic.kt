package com.music.spotui.data.local

import android.content.ContentUris
import android.content.Context
import android.provider.MediaStore
import com.music.spotui.data.entity.SongsModel

object MediaStoreLocalMusic {
    fun search(context: Context, query: String): List<SongsModel> {
        val p=arrayOf(MediaStore.Audio.Media._ID,MediaStore.Audio.Media.TITLE,MediaStore.Audio.Media.ARTIST,MediaStore.Audio.Media.ALBUM,MediaStore.Audio.Media.DURATION,MediaStore.Audio.Media.ALBUM_ID)
        val s=buildString{append("${MediaStore.Audio.Media.IS_MUSIC} != 0");if(query.isNotBlank())append(" AND (${MediaStore.Audio.Media.TITLE} LIKE ? OR ${MediaStore.Audio.Media.ARTIST} LIKE ? OR ${MediaStore.Audio.Media.ALBUM} LIKE ?)")}
        val a=if(query.isBlank())null else arrayOf("%$query%","%$query%","%$query%")
        return buildList{context.contentResolver.query(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,p,s,a,"${MediaStore.Audio.Media.TITLE} COLLATE NOCASE ASC")?.use{c->
            val id=c.getColumnIndexOrThrow(MediaStore.Audio.Media._ID);val title=c.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE);val artist=c.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST);val album=c.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM);val duration=c.getColumnIndexOrThrow(MediaStore.Audio.Media.DURATION);val albumId=c.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM_ID)
            while(c.moveToNext()){val mediaId=c.getLong(id);val uri=ContentUris.withAppendedId(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,mediaId);val aid=c.getLong(albumId);val cover=if(aid>0)"content://media/external/audio/albumart/$aid" else "";add(SongsModel(mediaId.toInt(),c.getString(title).orEmpty().ifBlank{"Unknown title"},c.getString(album).orEmpty(),c.getString(artist).orEmpty().ifBlank{"Unknown artist"},cover,uri.toString(),"",false,c.getLong(duration).toInt()))}
        }}
    }
}
