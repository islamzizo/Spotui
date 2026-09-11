package com.music.spotui.ui.screens

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.music.spotui.data.entity.SongsModel
import com.music.spotui.data.local.MediaStoreLocalMusic
import com.music.spotui.data.preferences.getLocalSongs
import com.music.spotui.di.SongPlayer
import com.music.spotui.ui.theme.AppBackground
import com.music.spotui.ui.theme.AppPalette
import com.music.spotui.ui.viewmodel.PlayerViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LocalFilesScreen(navController:NavController){
    val c=LocalContext.current;val vm:PlayerViewModel=hiltViewModel();var q by remember{mutableStateOf("")};var results by remember{mutableStateOf(emptyList<SongsModel>())};var imported by remember{mutableStateOf(getLocalSongs(c))};var granted by remember{mutableStateOf(false)}
    fun refresh(){if(granted){results=MediaStoreLocalMusic.search(c,q);imported=getLocalSongs(c)}}
    val permission=rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()){granted=it;refresh()}
    LaunchedEffect(Unit){val p=if(Build.VERSION.SDK_INT>=33)Manifest.permission.READ_MEDIA_AUDIO else Manifest.permission.READ_EXTERNAL_STORAGE;granted=androidx.core.content.ContextCompat.checkSelfPermission(c,p)==android.content.pm.PackageManager.PERMISSION_GRANTED;if(!granted)permission.launch(p)else refresh()}
    Scaffold(containerColor=AppBackground,topBar={TopAppBar(title={Text("Local music",color=Color.White)},navigationIcon={Icon(Icons.AutoMirrored.Filled.ArrowBack,"Back",tint=Color.White,modifier=Modifier.clickable{navController.navigateUp()})},colors=TopAppBarDefaults.topAppBarColors(containerColor=AppBackground))}){pad->Column(Modifier.fillMaxSize().padding(pad)){
        OutlinedTextField(value=q,onValueChange={q=it;results=if(granted)MediaStoreLocalMusic.search(c,it)else emptyList()},singleLine=true,label={Text("Search device music")},modifier=Modifier.fillMaxWidth().padding(16.dp))
        if(!granted){Text("Music permission is required to search files on this device.",color=Color.LightGray,modifier=Modifier.padding(horizontal=16.dp));Text("Allow access",color=AppPalette,modifier=Modifier.clickable{val p=if(Build.VERSION.SDK_INT>=33)Manifest.permission.READ_MEDIA_AUDIO else Manifest.permission.READ_EXTERNAL_STORAGE;permission.launch(p)}.padding(16.dp))}
        LazyColumn(contentPadding=PaddingValues(bottom=120.dp)){
            if(q.isBlank()&&imported.isNotEmpty()){item{Text("Imported local files",color=Color.White,fontSize=18.sp,modifier=Modifier.padding(16.dp))};items(imported.size){i->LocalRow(imported[i],i,imported,vm,c)}}
            item{Text(if(q.isBlank())"Device library" else "Device results",color=Color.White,fontSize=18.sp,modifier=Modifier.padding(16.dp))};items(results.size){i->LocalRow(results[i],i,results,vm,c)}
        }
    }}
}

@Composable private fun LocalRow(song:SongsModel,index:Int,list:List<SongsModel>,vm:PlayerViewModel,c:android.content.Context){Row(Modifier.fillMaxWidth().clickable{vm.updateQueue(list);vm.updateSongState(song.coverUri,song.title,song.singer,true,song.id,index,song.album);SongPlayer.playSong(song.url,c)}.padding(16.dp,10.dp),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text(song.title,color=Color.White,maxLines=1);Text(listOf(song.singer,song.album).filter{it.isNotBlank()}.joinToString(" • "),color=Color.Gray,fontSize=12.sp,maxLines=1)};Text("LOCAL",color=AppPalette,fontSize=10.sp)}}
