package com.music.spotui.ui.navigation

import android.os.Build
import androidx.annotation.RequiresApi
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.music.spotui.data.api.SpotifySession
import com.music.spotui.ui.screens.*
import com.music.spotui.ui.viewmodel.PlayerViewModel

@RequiresApi(Build.VERSION_CODES.S)
@Composable
fun MyNavHost(navHostController:NavHostController,bottomBarState:MutableState<Boolean>,bottomBarPlayerState:MutableState<Boolean>){
    val vm:PlayerViewModel=hiltViewModel();val playerState by vm.currentSongTitle;val context=LocalContext.current
    val start=if(SpotifySession.spDc(context).isBlank())Routes.Login.route else Routes.Home.route
    LaunchedEffect(Unit){if(vm.currentSongTitle.value.isBlank())com.music.spotui.data.preferences.loadLastPlayback(context)?.let{(song,pos)->vm.updateQueue(listOf(song));vm.updateSongState(song.coverUri,song.title,song.singer,false,song.id,0,song.album);com.music.spotui.di.SongPlayer.setRestorePoint(song.url,pos)}}
    NavHost(navHostController,start,enterTransition={fadeIn(tween(150))},exitTransition={fadeOut(tween(150))},popEnterTransition={fadeIn(tween(150))},popExitTransition={fadeOut(tween(150))}){
        composable(Routes.Login.route){LaunchedEffect(Unit){bottomBarState.value=false;bottomBarPlayerState.value=false};SpotifyLoginScreen(navHostController)}
        composable(Routes.Home.route){LaunchedEffect(playerState){bottomBarState.value=true;bottomBarPlayerState.value=playerState.isNotBlank()};HomeScreen(navHostController)}
        composable(Routes.Search.route){LaunchedEffect(playerState){bottomBarState.value=true;bottomBarPlayerState.value=playerState.isNotBlank()};SearchScreen(navHostController)}
        composable(Routes.Library.route){LaunchedEffect(playerState){bottomBarState.value=true;bottomBarPlayerState.value=playerState.isNotBlank()};LibraryScreen(navHostController)}
        composable(Routes.Player.route){LaunchedEffect(playerState){bottomBarState.value=false;bottomBarPlayerState.value=playerState.isNotBlank()};PlayerScreen(navHostController)}
        composable(Routes.Queue.route){LaunchedEffect(Unit){bottomBarState.value=false;bottomBarPlayerState.value=false};QueueScreen(navHostController)}
        composable(Routes.Liked.route){LikedSongsScreen(navHostController)}
        composable(Routes.Downloads.route){DownloadsScreen(navHostController)}
        composable(Routes.Settings.route){SettingsScreen(navHostController)}
        composable(Routes.History.route){HistoryScreen(navHostController)}
        composable(Routes.MusicSource.route){MusicSourceScreen(navHostController)}
        composable(Routes.LocalFiles.route){LocalFilesScreen(navHostController)}
        composable("${Routes.Category.route}/{genre}?title={title}",arguments=listOf(navArgument("title"){defaultValue=""})){e->CategoryScreen(navHostController,e.arguments?.getString("genre").orEmpty(),e.arguments?.getString("title").orEmpty())}
        composable("${Routes.Album.route}/{uString}?artist={artist}",arguments=listOf(navArgument("artist"){defaultValue=""})){e->e.arguments?.getString("uString")?.let{AlbumScreen(navHostController,it,e.arguments?.getString("artist").orEmpty())}}
        composable("${Routes.Playlist.route}/{pId}?name={name}",arguments=listOf(navArgument("name"){defaultValue=""})){e->e.arguments?.getString("pId")?.let{PlaylistScreen(navHostController,it,e.arguments?.getString("name").orEmpty())}}
        composable("${Routes.Show.route}/{sId}?name={name}",arguments=listOf(navArgument("name"){defaultValue=""})){e->e.arguments?.getString("sId")?.let{ShowScreen(navHostController,it,e.arguments?.getString("name").orEmpty())}}
        composable("${Routes.ArtistReleases.route}/{aString}"){e->e.arguments?.getString("aString")?.let{ArtistReleasesScreen(navHostController,it)}}
        composable("${Routes.Artist.route}/{aString}?id={artistId}",arguments=listOf(navArgument("artistId"){defaultValue=""})){e->e.arguments?.getString("aString")?.let{ArtistScreen(navHostController,it,e.arguments?.getString("artistId").orEmpty())}}
    }
}
