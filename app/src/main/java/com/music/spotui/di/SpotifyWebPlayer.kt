package com.music.spotui.di

import android.app.Activity
import android.content.Context

/** Compatibility shim only. No WebView, Spotify web playback, DRM, or network audio is used. */
object SpotifyWebPlayer {
    @Volatile var canPlay=false
    @Volatile var pageReady=false
    @Volatile var positionMs=0L
    @Volatile var durationMs=0L
    @Volatile var isPlaying=false
    @Volatile var onStateChanged:(()->Unit)?=null
    fun attach(activity:Activity)=Unit
    fun refreshLogin(context:Context)=Unit
    fun play(trackId:String)=Unit
    fun playEpisode(episodeId:String)=Unit
    fun resume()=Unit
    fun pause()=Unit
    fun next()=Unit
    fun previous()=Unit
    fun seekTo(positionMs:Long)=Unit
    fun detach()=Unit
    fun release()=Unit
}
