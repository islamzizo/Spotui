package com.music.spotui.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.music.spotui.data.preferences.MusicSource
import com.music.spotui.data.preferences.setPrimaryMusicSource
import com.music.spotui.ui.navigation.Routes

@Composable
fun MusicSourceScreen(navController:NavController){
    val context=androidx.compose.ui.platform.LocalContext.current
    setPrimaryMusicSource(context,MusicSource.MONOCHROME)
    Box(Modifier.fillMaxSize().background(Color.Black),contentAlignment=Alignment.Center){Column(Modifier.padding(24.dp),horizontalAlignment=Alignment.CenterHorizontally){Text("Monochrome",color=Color.White,fontSize=28.sp);Spacer(Modifier.height(12.dp));Text("Spotify provides metadata and your library. Monochrome is the sole online audio backend.",color=Color.LightGray,fontSize=14.sp);Spacer(Modifier.height(24.dp));Text("Continue",color=Color.White,fontSize=16.sp,modifier=Modifier.clickable{navController.navigate(Routes.Home.route){popUpTo(Routes.MusicSource.route){inclusive=true}}}.padding(16.dp))}}
}
