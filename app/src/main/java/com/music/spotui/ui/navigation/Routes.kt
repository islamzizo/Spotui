package com.music.spotui.ui.navigation

import androidx.annotation.DrawableRes
import com.music.spotui.R

sealed class Routes(@DrawableRes val icon:Int=0,val label:String,val route:String){
    object Home:Routes(R.drawable.ic_home_filled,"Home","home"); object Search:Routes(R.drawable.ic_search_big,"Search","search"); object Library:Routes(R.drawable.ic_library_big,"Library","library")
    object Album:Routes(0,"Album","album"); object Player:Routes(0,"Player","player"); object Artist:Routes(0,"Artist","artist"); object ArtistReleases:Routes(0,"ArtistReleases","artistreleases"); object Playlist:Routes(0,"Playlist","playlist"); object Show:Routes(0,"Show","show"); object Queue:Routes(0,"Queue","queue"); object Liked:Routes(0,"Liked","liked"); object Downloads:Routes(0,"Downloads","downloads"); object Category:Routes(0,"Category","category"); object Login:Routes(0,"Login","login"); object Settings:Routes(0,"Settings","settings"); object History:Routes(0,"History","history"); object MusicSource:Routes(0,"MusicSource","musicsource"); object LocalFiles:Routes(0,"LocalFiles","localfiles")
}
fun categoryRoute(g:String,t:String)="${Routes.Category.route}/${android.net.Uri.encode(g)}?title=${android.net.Uri.encode(t)}"
fun playlistRoute(id:String,name:String="")="${Routes.Playlist.route}/${android.net.Uri.encode(id)}?name=${android.net.Uri.encode(name)}"
fun showRoute(id:String,name:String="")="${Routes.Show.route}/${android.net.Uri.encode(id)}?name=${android.net.Uri.encode(name)}"
fun artistRoute(name:String,id:String="") { val b="${Routes.Artist.route}/${android.net.Uri.encode(name)}"; return if(id.isBlank())b else "$b?id=${android.net.Uri.encode(id)}" }
fun albumRoute(name:String,artist:String="") { val b="${Routes.Album.route}/$name"; return if(artist.isBlank())b else "$b?artist=${android.net.Uri.encode(artist)}" }
