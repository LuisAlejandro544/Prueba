package com.example.ui.components

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Layers
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.example.data.model.Country
import com.example.data.model.Province
import com.example.ui.theme.StrategyDarkBg
import com.example.ui.theme.StrategyGold
import com.example.ui.theme.StrategyMapOcean
import com.example.ui.theme.StrategySurface
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Visor interactivo para examinar el mapa original Blank_province_map.png
 * con zoom libre, paneo y opción de ver la capa de Latinoamérica superpuesta.
 */
@Composable
fun FullMapViewerDialog(
    provinces: List<Province>,
    countries: List<Country>,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var mapBitmap by remember { mutableStateOf<ImageBitmap?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var isPoliticalMap by remember { mutableStateOf(true) }
    var showProvincesOverlay by remember { mutableStateOf(false) }

    var scale by remember { mutableFloatStateOf(1.0f) }
    var offset by remember { mutableStateOf(Offset(0f, 0f)) }

    val countryMap = remember(countries) { countries.associateBy { it.id } }

    LaunchedEffect(isPoliticalMap) {
        isLoading = true
        withContext(Dispatchers.IO) {
            try {
                val assetName = if (isPoliticalMap) "political_province_map.png" else "blank_province_map.png"
                context.assets.open(assetName).use { stream ->
                    val options = BitmapFactory.Options().apply {
                        inPreferredConfig = Bitmap.Config.RGB_565
                        inSampleSize = if (isPoliticalMap) 1 else 2
                    }
                    val bmp = BitmapFactory.decodeStream(stream, null, options)
                    bmp?.let {
                        mapBitmap = it.asImageBitmap()
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                isLoading = false
            }
        }
    }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(
            usePlatformDefaultWidth = false,
            dismissOnBackPress = true
        )
    ) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = StrategyDarkBg
        ) {
            Box(modifier = Modifier.fillMaxSize()) {
                if (isLoading) {
                    Column(
                        modifier = Modifier.align(Alignment.Center),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator(color = StrategyGold)
                        Spacer(modifier = Modifier.size(12.dp))
                        Text(
                            text = "Cargando Blank_province_map.png...",
                            color = Color.White,
                            fontSize = 14.sp
                        )
                    }
                } else if (mapBitmap != null) {
                    val bmp = mapBitmap!!
                    val imageWidth = bmp.width.toFloat()
                    val imageHeight = bmp.height.toFloat()

                    Canvas(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(StrategyMapOcean)
                            .pointerInput(Unit) {
                                detectTransformGestures { _, pan, zoom, _ ->
                                    scale = (scale * zoom).coerceIn(0.4f, 6.0f)
                                    offset += pan
                                }
                            }
                    ) {
                        val canvasW = size.width
                        val canvasH = size.height

                        // Calculate aspect ratio fit
                        val mapAspect = imageWidth / imageHeight
                        val canvasAspect = canvasW / canvasH
                        val baseScale = if (canvasAspect > mapAspect) {
                            canvasH / imageHeight
                        } else {
                            canvasW / imageWidth
                        }

                        val mapDisplayW = imageWidth * baseScale
                        val mapDisplayH = imageHeight * baseScale
                        val baseLeft = (canvasW - mapDisplayW) / 2f
                        val baseTop = (canvasH - mapDisplayH) / 2f

                        withTransform({
                            translate(left = offset.x, top = offset.y)
                            scale(scaleX = scale, scaleY = scale, pivot = Offset(canvasW / 2f, canvasH / 2f))
                        }) {
                            // 1. Draw the actual Blank_province_map.png
                            drawImage(
                                image = bmp,
                                srcOffset = IntOffset.Zero,
                                srcSize = IntSize(bmp.width, bmp.height),
                                dstOffset = IntOffset(baseLeft.toInt(), baseTop.toInt()),
                                dstSize = IntSize(mapDisplayW.toInt(), mapDisplayH.toInt())
                            )

                            // 2. Optional Latin America provinces layer overlay
                            if (showProvincesOverlay) {
                                for (prov in provinces) {
                                    val country = countryMap[prov.ownerCountryId]
                                    val color = country?.primaryColor ?: Color.Gray

                                    val cx = baseLeft + prov.centerNormalizedX * mapDisplayW
                                    val cy = baseTop + prov.centerNormalizedY * mapDisplayH

                                    drawCircle(
                                        color = color.copy(alpha = 0.85f),
                                        radius = 12f * (scale.coerceAtMost(2.5f)),
                                        center = Offset(cx, cy)
                                    )
                                    drawCircle(
                                        color = Color.Black,
                                        radius = 13f * (scale.coerceAtMost(2.5f)),
                                        center = Offset(cx, cy),
                                        style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2f)
                                    )
                                }
                            }
                        }
                    }
                }

                // Top Controls Bar
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .align(Alignment.TopCenter),
                    color = StrategySurface.copy(alpha = 0.92f)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.Layers,
                                contentDescription = null,
                                tint = StrategyGold,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Column {
                                Text(
                                    text = "Blank_province_map.png (5632 x 2048)",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 14.sp,
                                    color = Color.White
                                )
                                Text(
                                    text = "Mapa de provincias auténtico de Age of History",
                                    fontSize = 11.sp,
                                    color = Color.LightGray
                                )
                            }
                        }

                        Row(verticalAlignment = Alignment.CenterVertically) {
                            FilterChip(
                                selected = isPoliticalMap,
                                onClick = { isPoliticalMap = !isPoliticalMap },
                                label = { Text(if (isPoliticalMap) "Mapa Político" else "Mapa en Blanco", fontSize = 11.sp) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = StrategyGold.copy(alpha = 0.3f),
                                    selectedLabelColor = StrategyGold
                                )
                            )

                            Spacer(modifier = Modifier.width(8.dp))

                            FilterChip(
                                selected = showProvincesOverlay,
                                onClick = { showProvincesOverlay = !showProvincesOverlay },
                                label = { Text("Puntos Estratégicos", fontSize = 11.sp) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = Color(0xFF3B82F6).copy(alpha = 0.3f),
                                    selectedLabelColor = Color(0xFF60A5FA)
                                )
                            )

                            Spacer(modifier = Modifier.width(12.dp))

                            IconButton(
                                onClick = onDismiss,
                                colors = IconButtonDefaults.iconButtonColors(
                                    containerColor = Color(0x33FFFFFF)
                                )
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Close,
                                    contentDescription = "Cerrar visor",
                                    tint = Color.White
                                )
                            }
                        }
                    }
                }

                // Floating Zoom / Re-center Controls
                Column(
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    IconButton(
                        onClick = { scale = (scale * 1.3f).coerceAtMost(6.0f) },
                        modifier = Modifier
                            .size(42.dp)
                            .background(StrategySurface.copy(alpha = 0.9f), CircleShape)
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "Acercar", tint = StrategyGold)
                    }

                    IconButton(
                        onClick = { scale = (scale / 1.3f).coerceAtLeast(0.4f) },
                        modifier = Modifier
                            .size(42.dp)
                            .background(StrategySurface.copy(alpha = 0.9f), CircleShape)
                    ) {
                        Icon(Icons.Default.Remove, contentDescription = "Alejar", tint = StrategyGold)
                    }

                    IconButton(
                        onClick = {
                            scale = 1.0f
                            offset = Offset(0f, 0f)
                        },
                        modifier = Modifier
                            .size(42.dp)
                            .background(StrategySurface.copy(alpha = 0.9f), CircleShape)
                    ) {
                        Icon(Icons.Default.MyLocation, contentDescription = "Centrar", tint = StrategyGold)
                    }
                }
            }
        }
    }
}
