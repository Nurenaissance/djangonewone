package com.whatsapp.business.automation

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

@SuppressLint("CustomSplashScreen")
class SplashActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SplashScreen {
                startActivity(Intent(this, MainActivity::class.java))
                finish()
            }
        }
    }
}

@Composable
fun SplashScreen(onTimeout: () -> Unit) {
    // Animation values
    val infiniteTransition = rememberInfiniteTransition(label = "splash")

    val scale by infiniteTransition.animateFloat(
        initialValue = 0.8f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )

    // Gradient colors - Nuren AI branding
    val gradientColors = listOf(
        Color(0xFF2563EB),  // Modern Blue
        Color(0xFF7C3AED),  // Purple
        Color(0xFF4F46E5)   // Indigo
    )

    LaunchedEffect(Unit) {
        delay(2500) // Show splash for 2.5 seconds
        onTimeout()
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                brush = Brush.verticalGradient(
                    colors = gradientColors
                )
            ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // App Icon/Logo (using emoji for now - replace with actual logo)
            Text(
                text = "🚀",
                fontSize = 120.sp,
                modifier = Modifier
                    .scale(scale)
                    .alpha(alpha)
            )

            Spacer(modifier = Modifier.height(32.dp))

            // App Name
            Text(
                text = "Nuren AI",
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                textAlign = TextAlign.Center,
                modifier = Modifier.alpha(alpha)
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Interview Platform",
                fontSize = 24.sp,
                fontWeight = FontWeight.Light,
                color = Color.White.copy(alpha = 0.9f),
                textAlign = TextAlign.Center,
                modifier = Modifier.alpha(alpha)
            )

            Spacer(modifier = Modifier.height(48.dp))

            // Loading indicator
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.alpha(alpha)
            ) {
                repeat(3) { index ->
                    val dotAlpha by infiniteTransition.animateFloat(
                        initialValue = 0.3f,
                        targetValue = 1f,
                        animationSpec = infiniteRepeatable(
                            animation = tween(
                                durationMillis = 600,
                                delayMillis = index * 200,
                                easing = LinearEasing
                            ),
                            repeatMode = RepeatMode.Reverse
                        ),
                        label = "dot_$index"
                    )

                    Box(
                        modifier = Modifier
                            .size(12.dp)
                            .alpha(dotAlpha)
                            .background(
                                color = Color.White,
                                shape = MaterialTheme.shapes.small
                            )
                    )
                }
            }
        }

        // Footer text
        Text(
            text = "Powered by Nuren AI",
            fontSize = 14.sp,
            fontWeight = FontWeight.Light,
            color = Color.White.copy(alpha = 0.7f),
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 48.dp)
                .alpha(alpha)
        )
    }
}
