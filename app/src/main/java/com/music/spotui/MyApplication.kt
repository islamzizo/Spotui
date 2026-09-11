package com.music.spotui

import android.app.Application
import com.music.spotui.data.api.Api
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import timber.log.Timber

@HiltAndroidApp
class MyApplication : Application() {
    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    companion object { @JvmStatic lateinit var instance: MyApplication; private set }

    override fun onCreate() {
        super.onCreate(); instance = this
        if (BuildConfig.DEBUG && Timber.forest().isEmpty()) Timber.plant(Timber.DebugTree())
        com.metrolist.spotify.Spotify.logger = { level, msg -> android.util.Log.d("SpotifyREST", "[$level] $msg") }
        com.metrolist.spotify.SpotifyCanvas.setLogger { level, msg -> android.util.Log.d("SpotifyCanvas", "[$level] $msg") }
        // Spotify is metadata/library only. Online audio is resolved exclusively by MonochromeClient.
        val api = Api(this)
        appScope.launch { runCatching { api.getHomeFeed().collect {} } }
        appScope.launch { runCatching { api.getAlbums().collect {} } }
        appScope.launch { runCatching { api.getArtists().collect {} } }
    }
}
