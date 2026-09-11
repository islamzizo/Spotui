package com.music.spotui

import android.content.ComponentName
import android.content.pm.ActivityInfo
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.RequiresApi
import androidx.core.content.ContextCompat
import androidx.media3.common.util.UnstableApi
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.google.common.util.concurrent.ListenableFuture
import com.music.spotui.di.SongPlayer
import com.music.spotui.ui.notification.PlaybackService
import com.music.spotui.ui.theme.SpotuiTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity:ComponentActivity(){
    private var controllerFuture:ListenableFuture<MediaController>?=null
    private val notificationPermission=registerForActivityResult(ActivityResultContracts.RequestPermission()){}
    @OptIn(UnstableApi::class)
    @RequiresApi(Build.VERSION_CODES.S)
    override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);requestedOrientation=ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.TIRAMISU&&ContextCompat.checkSelfPermission(this,android.Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)notificationPermission.launch(android.Manifest.permission.POST_NOTIFICATIONS)
        controllerFuture=MediaController.Builder(this,SessionToken(this,ComponentName(this,PlaybackService::class.java))).buildAsync()
        enableEdgeToEdge();if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.Q)window.isNavigationBarContrastEnforced=false
        setContent{SpotuiTheme{App();com.music.spotui.ui.components.UpdatePrompt()}}
    }
    override fun onDestroy(){controllerFuture?.let{MediaController.releaseFuture(it)};SongPlayer.release();super.onDestroy()}
}
