package com.music.spotui.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.music.spotui.data.api.Api
import com.music.spotui.data.api.SpotifySession
import com.music.spotui.data.preferences.*
import com.music.spotui.ui.navigation.Routes
import com.music.spotui.ui.theme.AppBackground
import com.music.spotui.ui.theme.AppPalette

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(navController:NavController){
    val c=androidx.compose.ui.platform.LocalContext.current
    var wifi by remember{mutableStateOf(getWifiQuality(c))};var cell by remember{mutableStateOf(getCellularQuality(c))};var dl by remember{mutableStateOf(getDownloadQuality(c))};var fade by remember{mutableStateOf(getCrossfadeMs(c).toFloat())}
    Scaffold(containerColor=AppBackground,topBar={CenterAlignedTopAppBar(title={Text("Settings",color=Color.White,fontWeight=FontWeight.Bold)},navigationIcon={Icon(Icons.AutoMirrored.Filled.ArrowBack,"Back",tint=Color.White,modifier=Modifier.clickable{navController.popBackStack()})},colors=TopAppBarDefaults.centerAlignedTopAppBarColors(containerColor=AppBackground))}){p->Column(Modifier.fillMaxSize().padding(p).verticalScroll(rememberScrollState()).padding(16.dp)){
        SectionTitle("Playback backend");Text("Monochrome",color=Color.White,fontSize=18.sp,fontWeight=FontWeight.Bold);Text("Sole online audio source. Spotui calls the Monochrome Hi-Fi API directly; its web frontend is not embedded.",color=Color.LightGray,fontSize=13.sp,modifier=Modifier.padding(top=4.dp))
        SectionTitle("Audio quality");QualityPicker("Streaming over Wi-Fi",wifi){wifi=it;setWifiQuality(c,it)};QualityPicker("Streaming over cellular",cell){cell=it;setCellularQuality(c,it)};QualityPicker("Download quality",dl){dl=it;setDownloadQuality(c,it)}
        SectionTitle("Crossfade");Text(if(fade<=0)"Off" else "${(fade/1000).toInt()}s",color=Color.White);Slider(value=fade,onValueChange={fade=it},onValueChangeFinished={setCrossfadeMs(c,fade.toInt())},valueRange=0f..CROSSFADE_MAX_MS.toFloat(),steps=(CROSSFADE_MAX_MS/1000)-1)
        SectionTitle("Local music");Text("Search device audio through Android MediaStore.",color=Color.LightGray,fontSize=13.sp);Text("Open Local music",color=AppPalette,fontWeight=FontWeight.Bold,modifier=Modifier.clickable{navController.navigate(Routes.LocalFiles.route)}.padding(vertical=12.dp))
        SectionTitle("Account");Text("Log out",color=Color(0xFFE57373),fontSize=16.sp,fontWeight=FontWeight.SemiBold,modifier=Modifier.fillMaxWidth().clickable{SpotifySession.setSpDc(c,"");Api.HomeCache.clear();navController.navigate(Routes.Login.route){popUpTo(0){inclusive=true}}}.padding(vertical=14.dp))
    }}
}
@Composable private fun SectionTitle(t:String){Text(t,color=AppPalette,fontSize=13.sp,fontWeight=FontWeight.Bold,modifier=Modifier.padding(top=16.dp,bottom=6.dp))}
@Composable private fun QualityPicker(title:String,selected:StreamQuality,onSelect:(StreamQuality)->Unit){Column(Modifier.padding(vertical=6.dp)){Text(title,color=Color.White,fontWeight=FontWeight.SemiBold);StreamQuality.entries.forEach{q->Row(Modifier.fillMaxWidth().clickable{onSelect(q)}.padding(12.dp),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text(q.label,color=Color.White);Text(q.detail,color=Color.LightGray,fontSize=12.sp)};if(q==selected)Icon(Icons.Default.Check,"Selected",tint=AppPalette)}}}}
