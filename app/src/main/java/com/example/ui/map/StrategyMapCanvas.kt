package com.example.ui.map

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Layers
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.model.ArmyMarch
import com.example.data.model.Country
import com.example.data.model.Province
import com.example.ui.theme.StrategyGold
import com.example.ui.theme.StrategyMapOcean
import com.example.ui.theme.StrategySurface
import com.example.ui.theme.WarRed
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlin.math.hypot

@Composable
fun StrategyMapCanvas(
    countries: List<Country>,
    provinces: List<Province>,
    activeMarches: List<ArmyMarch>,
    selectedProvince: Province?,
    playerCountry: Country?,
    onProvinceSelected: (Province) -> Unit,
    onOpenFullMapViewer: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var mapBitmap by remember { mutableStateOf<ImageBitmap?>(null) }

    // Map navigation state
    var scale by remember { mutableFloatStateOf(2.8f) }
    var offset by remember { mutableStateOf(Offset(0f, 0f)) }
    var hasCenteredInitially by remember { mutableStateOf(false) }
    var canvasSize by remember { mutableStateOf(Size.Zero) }

    val textMeasurer = rememberTextMeasurer()
    val countryMap = remember(countries) { countries.associateBy { it.id } }

    // Dimensión base del nuevo mapa mundial
    val defaultMapW = 4096f
    val defaultMapH = 1675f

    // Load world_provinces_political.png in background
    LaunchedEffect(Unit) {
        withContext(Dispatchers.IO) {
            try {
                val stream = context.assets.open("world_provinces_political.png")
                stream.use { s ->
                    val options = BitmapFactory.Options().apply {
                        inPreferredConfig = Bitmap.Config.RGB_565
                        inSampleSize = 1
                    }
                    val bmp = BitmapFactory.decodeStream(s, null, options)
                    bmp?.let {
                        mapBitmap = it.asImageBitmap()
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    // Helper to center the map on normalized coordinates
    fun centerOnNormalized(normX: Float, normY: Float, targetScale: Float = scale) {
        if (canvasSize.width <= 0f || canvasSize.height <= 0f) return
        val mapW = mapBitmap?.width?.toFloat() ?: defaultMapW
        val mapH = mapBitmap?.height?.toFloat() ?: defaultMapH
        val mapAspect = mapW / mapH
        val canvasAspect = canvasSize.width / canvasSize.height
        val baseScale = if (canvasAspect > mapAspect) {
            canvasSize.height / mapH
        } else {
            canvasSize.width / mapW
        }
        val mapDisplayW = mapW * baseScale
        val mapDisplayH = mapH * baseScale
        val baseLeft = (canvasSize.width - mapDisplayW) / 2f
        val baseTop = (canvasSize.height - mapDisplayH) / 2f

        val targetCenterX = baseLeft + normX * mapDisplayW
        val targetCenterY = baseTop + normY * mapDisplayH

        scale = targetScale
        offset = Offset(
            x = (canvasSize.width / 2f) - (targetCenterX * targetScale),
            y = (canvasSize.height / 2f) - (targetCenterY * targetScale)
        )
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(StrategyMapOcean)
    ) {
        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .pointerInput(Unit) {
                    detectTransformGestures { _, pan, zoom, _ ->
                        scale = (scale * zoom).coerceIn(0.8f, 7.0f)
                        offset += pan
                    }
                }
                .pointerInput(provinces, scale, offset) {
                    detectTapGestures { tapOffset ->
                        val canvasW = size.width
                        val canvasH = size.height

                        // Calculate base map dimensions
                        val mapW = mapBitmap?.width?.toFloat() ?: defaultMapW
                        val mapH = mapBitmap?.height?.toFloat() ?: defaultMapH
                        val mapAspect = mapW / mapH
                        val canvasAspect = canvasW / canvasH
                        val baseScale = if (canvasAspect > mapAspect) {
                            canvasH / mapH
                        } else {
                            canvasW / mapW
                        }
                        val mapDisplayW = mapW * baseScale
                        val mapDisplayH = mapH * baseScale
                        val baseLeft = (canvasW - mapDisplayW) / 2f
                        val baseTop = (canvasH - mapDisplayH) / 2f

                        // Inverse transform tap coordinate to world map normalized coordinate (0.0 to 1.0)
                        val virtualX = (tapOffset.x - offset.x) / scale
                        val virtualY = (tapOffset.y - offset.y) / scale

                        val normTapX = (virtualX - baseLeft) / mapDisplayW
                        val normTapY = (virtualY - baseTop) / mapDisplayH

                        // 1. Detección precisa de toque dentro del polígono territorial (Point-in-Polygon)
                        var matchedProv: Province? = null
                        for (prov in provinces) {
                            if (prov.boundaryPointsNormalized.isNotEmpty() &&
                                isPointInPolygon(normTapX, normTapY, prov.boundaryPointsNormalized)
                            ) {
                                matchedProv = prov
                                break
                            }
                        }

                        // 2. Si no cayó dentro de un polígono cerrado estricto, buscar la provincia/país más cercano
                        if (matchedProv == null) {
                            var minDistance = Float.MAX_VALUE
                            val touchRadius = 0.065f // Radio táctil optimizado para pantallas táctiles móviles
                            for (prov in provinces) {
                                val dist = hypot(normTapX - prov.centerNormalizedX, normTapY - prov.centerNormalizedY)
                                if (dist < touchRadius && dist < minDistance) {
                                    minDistance = dist
                                    matchedProv = prov
                                }
                            }
                        }

                        if (matchedProv != null) {
                            onProvinceSelected(matchedProv)
                        }
                    }
                }
        ) {
            val canvasW = size.width
            val canvasH = size.height
            canvasSize = size

            val mapW = mapBitmap?.width?.toFloat() ?: defaultMapW
            val mapH = mapBitmap?.height?.toFloat() ?: defaultMapH
            val mapAspect = mapW / mapH
            val canvasAspect = canvasW / canvasH
            val baseScale = if (canvasAspect > mapAspect) canvasH / mapH else canvasW / mapW
            val mapDisplayW = mapW * baseScale
            val mapDisplayH = mapH * baseScale
            val baseLeft = (canvasW - mapDisplayW) / 2f
            val baseTop = (canvasH - mapDisplayH) / 2f

            // Initial center on player's nation capital
            if (!hasCenteredInitially && canvasW > 0 && canvasH > 0) {
                val playerProv = provinces.find { it.ownerCountryId == playerCountry?.id && it.isCapital }
                    ?: provinces.find { it.ownerCountryId == playerCountry?.id }

                val targetX = playerProv?.centerNormalizedX ?: 0.2095f
                val targetY = playerProv?.centerNormalizedY ?: 0.4150f

                val targetCenterX = baseLeft + targetX * mapDisplayW
                val targetCenterY = baseTop + targetY * mapDisplayH

                offset = Offset(
                    x = (canvasW / 2f) - (targetCenterX * scale),
                    y = (canvasH / 2f) - (targetCenterY * scale)
                )
                hasCenteredInitially = true
            }

            // 1. TRANSFORMED MAP LAYER (Base political map, borders, tactical lines, marches)
            withTransform({
                translate(left = offset.x, top = offset.y)
                scale(scaleX = scale, scaleY = scale, pivot = Offset.Zero)
            }) {
                // Draw the pre-colored authentic political province map
                val bmp = mapBitmap
                if (bmp != null) {
                    drawImage(
                        image = bmp,
                        srcOffset = IntOffset.Zero,
                        srcSize = IntSize(bmp.width, bmp.height),
                        dstOffset = IntOffset(baseLeft.toInt(), baseTop.toInt()),
                        dstSize = IntSize(mapDisplayW.toInt(), mapDisplayH.toInt())
                    )
                } else {
                    // Fallback ocean background
                    drawRect(
                        color = StrategyMapOcean,
                        topLeft = Offset(baseLeft, baseTop),
                        size = Size(mapDisplayW, mapDisplayH)
                    )
                    drawTacticalGrid(baseLeft, baseTop, mapDisplayW, mapDisplayH)
                }

                // Selected Province Tactical Glowing Indicator
                if (selectedProvince != null) {
                    val selX = baseLeft + selectedProvince.centerNormalizedX * mapDisplayW
                    val selY = baseTop + selectedProvince.centerNormalizedY * mapDisplayH
                    val haloRadius = (32f / scale).coerceIn(16f, 48f)

                    drawCircle(
                        color = StrategyGold.copy(alpha = 0.28f),
                        radius = haloRadius * 1.5f,
                        center = Offset(selX, selY)
                    )
                    drawCircle(
                        color = StrategyGold,
                        radius = haloRadius,
                        center = Offset(selX, selY),
                        style = Stroke(width = (2.5f / scale).coerceAtLeast(1.5f))
                    )
                }

                // Tactical Military Links between adjacent provinces
                for (prov in provinces) {
                    val p1X = baseLeft + prov.centerNormalizedX * mapDisplayW
                    val p1Y = baseTop + prov.centerNormalizedY * mapDisplayH

                    for (adjId in prov.adjacentProvinceIds) {
                        val adj = provinces.find { it.id == adjId }
                        if (adj != null && adj.id > prov.id) {
                            val p2X = baseLeft + adj.centerNormalizedX * mapDisplayW
                            val p2Y = baseTop + adj.centerNormalizedY * mapDisplayH

                            drawLine(
                                color = Color(0x33FFFFFF),
                                start = Offset(p1X, p1Y),
                                end = Offset(p2X, p2Y),
                                strokeWidth = (1f / scale).coerceAtLeast(0.6f),
                                pathEffect = PathEffect.dashPathEffect(floatArrayOf(4f, 4f), 0f)
                            )
                        }
                    }
                }

                // Active Troop Marches
                for (march in activeMarches) {
                    val fromProv = provinces.find { it.id == march.fromProvinceId }
                    val toProv = provinces.find { it.id == march.toProvinceId }

                    if (fromProv != null && toProv != null) {
                        val x1 = baseLeft + fromProv.centerNormalizedX * mapDisplayW
                        val y1 = baseTop + fromProv.centerNormalizedY * mapDisplayH
                        val x2 = baseLeft + toProv.centerNormalizedX * mapDisplayW
                        val y2 = baseTop + toProv.centerNormalizedY * mapDisplayH

                        drawLine(
                            color = if (march.ownerCountryId == playerCountry?.id) StrategyGold else WarRed,
                            start = Offset(x1, y1),
                            end = Offset(x2, y2),
                            strokeWidth = (2.5f / scale).coerceAtLeast(1.8f),
                            pathEffect = PathEffect.dashPathEffect(floatArrayOf(6f, 6f), 0f)
                        )

                        val currentX = x1 + (x2 - x1) * march.progress
                        val currentY = y1 + (y2 - y1) * march.progress
                        val armyRadius = (14f / scale).coerceIn(7f, 18f)

                        drawCircle(
                            color = Color.Black,
                            radius = armyRadius + 2f,
                            center = Offset(currentX, currentY)
                        )
                        drawCircle(
                            color = if (march.ownerCountryId == playerCountry?.id) StrategyGold else WarRed,
                            radius = armyRadius,
                            center = Offset(currentX, currentY)
                        )
                    }
                }
            }

            // 2. SCREEN-SPACE LABELS & BADGES (Anti-Inflation: Always compact and never occluding the map)
            for (prov in provinces) {
                val owner = countryMap[prov.ownerCountryId]
                val isSelected = selectedProvince?.id == prov.id
                val isPlayerOwned = prov.ownerCountryId == playerCountry?.id

                val virtualX = baseLeft + prov.centerNormalizedX * mapDisplayW
                val virtualY = baseTop + prov.centerNormalizedY * mapDisplayH

                // Project virtual coordinate into exact physical screen pixels
                val screenX = offset.x + virtualX * scale
                val screenY = offset.y + virtualY * scale

                // Viewport culling (skip drawing if outside screen view)
                if (screenX < -120f || screenX > canvasW + 120f || screenY < -80f || screenY > canvasH + 80f) {
                    continue
                }

                // Troop Pill Badge (Exact screen-space size, always sharp and small)
                val troopStr = "${owner?.flagEmoji ?: ""} ${formatTroopCount(prov.army)}"
                val troopTextLayout = textMeasurer.measure(
                    text = troopStr,
                    style = TextStyle(
                        color = Color.White,
                        fontSize = 10.5.sp,
                        fontWeight = FontWeight.Bold
                    )
                )

                val badgeW = troopTextLayout.size.width + 14f
                val badgeH = troopTextLayout.size.height + 6f
                val badgeLeft = screenX - (badgeW / 2f)
                val badgeTop = screenY - (badgeH / 2f)

                // Compact Badge outline
                drawRoundRect(
                    color = if (isSelected) StrategyGold else if (isPlayerOwned) Color(0xFF60A5FA) else Color(0x99000000),
                    topLeft = Offset(badgeLeft - 1.5f, badgeTop - 1.5f),
                    size = Size(badgeW + 3f, badgeH + 3f),
                    cornerRadius = CornerRadius(6f, 6f)
                )

                // Compact Badge fill
                drawRoundRect(
                    brush = Brush.verticalGradient(
                        colors = if (isPlayerOwned) listOf(Color(0xFF1E3A8A), Color(0xFF0F172A))
                        else listOf(Color(0xF01E293B), Color(0xF00F172A))
                    ),
                    topLeft = Offset(badgeLeft, badgeTop),
                    size = Size(badgeW, badgeH),
                    cornerRadius = CornerRadius(5f, 5f)
                )

                // Troop text
                drawText(
                    textLayoutResult = troopTextLayout,
                    topLeft = Offset(badgeLeft + 7f, badgeTop + 3f)
                )

                // Province Name: Only show when zoomed in or when selected, with a subtle tiny label
                if (isSelected || (scale >= 2.0f && prov.isCapital) || scale >= 3.0f) {
                    val nameStr = if (prov.isCapital) "★ ${prov.name}" else prov.name
                    val nameTextLayout = textMeasurer.measure(
                        text = nameStr,
                        style = TextStyle(
                            color = if (isSelected) StrategyGold else Color(0xFFF1F5F9),
                            fontSize = 9.sp,
                            fontWeight = if (prov.isCapital || isSelected) FontWeight.Bold else FontWeight.Normal
                        )
                    )

                    val labelLeft = screenX - (nameTextLayout.size.width / 2f)
                    val labelTop = badgeTop + badgeH + 2f

                    // Discreet translucent label background (never obscures the green or territory)
                    drawRoundRect(
                        color = Color(0xCC0F172A),
                        topLeft = Offset(labelLeft - 4f, labelTop - 1f),
                        size = Size(nameTextLayout.size.width + 8f, nameTextLayout.size.height + 2f),
                        cornerRadius = CornerRadius(4f, 4f)
                    )

                    drawText(
                        textLayoutResult = nameTextLayout,
                        topLeft = Offset(labelLeft, labelTop)
                    )
                }
            }
        }

        // Floating On-Screen Map Controls (Bottom-Left)
        Column(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Zoom In
            IconButton(
                onClick = { scale = (scale * 1.3f).coerceAtMost(7.0f) },
                modifier = Modifier
                    .size(40.dp)
                    .background(StrategySurface.copy(alpha = 0.9f), CircleShape),
                colors = IconButtonDefaults.iconButtonColors(contentColor = StrategyGold)
            ) {
                Icon(Icons.Default.Add, contentDescription = "Acercar mapa")
            }

            // Zoom Out
            IconButton(
                onClick = { scale = (scale / 1.3f).coerceAtLeast(0.8f) },
                modifier = Modifier
                    .size(40.dp)
                    .background(StrategySurface.copy(alpha = 0.9f), CircleShape),
                colors = IconButtonDefaults.iconButtonColors(contentColor = StrategyGold)
            ) {
                Icon(Icons.Default.Remove, contentDescription = "Alejar mapa")
            }

            // Center on Player Nation
            IconButton(
                onClick = {
                    val playerProv = provinces.find { it.ownerCountryId == playerCountry?.id && it.isCapital }
                        ?: provinces.find { it.ownerCountryId == playerCountry?.id }
                    if (playerProv != null) {
                        centerOnNormalized(playerProv.centerNormalizedX, playerProv.centerNormalizedY, 3.0f)
                    }
                },
                modifier = Modifier
                    .size(40.dp)
                    .background(StrategySurface.copy(alpha = 0.9f), CircleShape),
                colors = IconButtonDefaults.iconButtonColors(contentColor = StrategyGold)
            ) {
                Icon(Icons.Default.MyLocation, contentDescription = "Mi Capital")
            }

            // Open Full Map Viewer
            IconButton(
                onClick = onOpenFullMapViewer,
                modifier = Modifier
                    .size(40.dp)
                    .background(StrategySurface.copy(alpha = 0.9f), CircleShape),
                colors = IconButtonDefaults.iconButtonColors(contentColor = Color(0xFF60A5FA))
            ) {
                Icon(Icons.Default.Layers, contentDescription = "Ver Mapa Completo")
            }
        }
    }
}

private fun DrawScope.drawTacticalGrid(left: Float, top: Float, width: Float, height: Float) {
    val step = 80f
    var x = left
    while (x <= left + width) {
        drawLine(
            color = Color(0x0EFFFFFF),
            start = Offset(x, top),
            end = Offset(x, top + height),
            strokeWidth = 1f
        )
        x += step
    }
    var y = top
    while (y <= top + height) {
        drawLine(
            color = Color(0x0EFFFFFF),
            start = Offset(left, y),
            end = Offset(left + width, y),
            strokeWidth = 1f
        )
        y += step
    }
}

private fun formatTroopCount(troops: Long): String {
    return when {
        troops >= 1_000_000 -> String.format("%.1fM", troops / 1_000_000.0)
        troops >= 1_000 -> String.format("%.1fK", troops / 1_000.0)
        else -> troops.toString()
    }
}

/**
 * Algoritmo de Ray-Casting para determinar si un punto táctil (px, py)
 * cae dentro del polígono delimitador de una provincia.
 */
private fun isPointInPolygon(px: Float, py: Float, polygon: List<Pair<Float, Float>>): Boolean {
    if (polygon.size < 3) return false
    var inside = false
    var j = polygon.size - 1
    for (i in polygon.indices) {
        val (xi, yi) = polygon[i]
        val (xj, yj) = polygon[j]
        val intersect = ((yi > py) != (yj > py)) &&
                (px < (xj - xi) * (py - yi) / (yj - yi) + xi)
        if (intersect) {
            inside = !inside
        }
        j = i
    }
    return inside
}
