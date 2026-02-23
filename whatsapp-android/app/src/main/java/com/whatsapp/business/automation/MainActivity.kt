package com.whatsapp.business.automation

import android.annotation.SuppressLint
import android.graphics.Bitmap
import android.os.Bundle
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.google.accompanist.swiperefresh.SwipeRefresh
import com.google.accompanist.swiperefresh.SwipeRefreshIndicator
import com.google.accompanist.swiperefresh.rememberSwipeRefreshState
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            WhatsAppBusinessTheme {
                MainScreen()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen() {
    var isLoading by remember { mutableStateOf(true) }
    var hasError by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }
    var webView: WebView? by remember { mutableStateOf(null) }
    var isRefreshing by remember { mutableStateOf(false) }
    var canGoBack by remember { mutableStateOf(false) }
    var contentVisible by remember { mutableStateOf(false) }

    // Web URL - Change this to your deployed React app URL
    val webUrl = "https://www.nuren.ai/"  // Your production URL

    // Animate content visibility
    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay(300)
        contentVisible = true
    }

    // Handle Android back button
    BackHandler(enabled = canGoBack) {
        webView?.goBack()
    }

    Box(modifier = Modifier.fillMaxSize()) {
        AnimatedVisibility(
            visible = contentVisible,
            enter = fadeIn(animationSpec = tween(600, easing = FastOutSlowInEasing)),
            exit = fadeOut(animationSpec = tween(400))
        ) {
            SwipeRefresh(
                state = rememberSwipeRefreshState(isRefreshing),
                onRefresh = {
                    isRefreshing = true
                    webView?.reload()
                },
                modifier = Modifier.fillMaxSize(),
                indicator = { state, trigger ->
                    SwipeRefreshIndicator(
                        state = state,
                        refreshTriggerDistance = trigger,
                        scale = true,
                        backgroundColor = MaterialTheme.colorScheme.surface,
                        contentColor = MaterialTheme.colorScheme.primary,
                        shape = MaterialTheme.shapes.small,
                    )
                }
            ) {
                AnimatedContent(
                    targetState = hasError,
                    transitionSpec = {
                        fadeIn(animationSpec = tween(400)) togetherWith
                                fadeOut(animationSpec = tween(400))
                    },
                    label = "content_transition"
                ) { error ->
                    if (error) {
                        // Error state - Show friendly error message
                        ErrorScreen(
                            errorMessage = errorMessage,
                            onRetry = {
                                hasError = false
                                isLoading = true
                                webView?.reload()
                            }
                        )
                    } else {
                        // WebView
                        WebViewComposable(
                            url = webUrl,
                            onWebViewCreated = { wv ->
                                webView = wv
                            },
                            onPageStarted = {
                                isLoading = true
                            },
                            onPageFinished = {
                                isLoading = false
                                isRefreshing = false
                                webView?.let {
                                    canGoBack = it.canGoBack()
                                }
                            },
                            onError = { message ->
                                hasError = true
                                errorMessage = message
                                isLoading = false
                                isRefreshing = false
                            },
                            onProgressChanged = { progress ->
                                // You can track progress here if needed
                            }
                        )
                    }
                }
            }
        }

        // Smooth loading indicator with gradient
        AnimatedVisibility(
            visible = isLoading && !hasError,
            enter = fadeIn(animationSpec = tween(300)) + scaleIn(
                animationSpec = tween(300, easing = FastOutSlowInEasing),
                initialScale = 0.8f
            ),
            exit = fadeOut(animationSpec = tween(300)) + scaleOut(
                animationSpec = tween(300, easing = FastOutSlowInEasing),
                targetScale = 0.8f
            )
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(
                        brush = Brush.verticalGradient(
                            colors = listOf(
                                MaterialTheme.colorScheme.background.copy(alpha = 0.95f),
                                MaterialTheme.colorScheme.surface.copy(alpha = 0.95f)
                            )
                        )
                    ),
                contentAlignment = Alignment.Center
            ) {
                LoadingAnimation()
            }
        }
    }
}

@Composable
fun LoadingAnimation() {
    val infiniteTransition = rememberInfiniteTransition(label = "loading")

    val rotation by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "rotation"
    )

    val scale by infiniteTransition.animateFloat(
        initialValue = 0.9f,
        targetValue = 1.1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator(
            modifier = Modifier
                .size(64.dp)
                .scale(scale),
            color = MaterialTheme.colorScheme.primary,
            strokeWidth = 4.dp,
            trackColor = MaterialTheme.colorScheme.primaryContainer
        )
        Spacer(modifier = Modifier.height(24.dp))
        Text(
            text = "Loading your workspace...",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onBackground,
            fontWeight = FontWeight.Medium
        )
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun WebViewComposable(
    url: String,
    onWebViewCreated: (WebView) -> Unit,
    onPageStarted: () -> Unit,
    onPageFinished: () -> Unit,
    onError: (String) -> Unit,
    onProgressChanged: (Int) -> Unit
) {
    val context = LocalContext.current

    AndroidView(
        factory = { ctx ->
            WebView(ctx).apply {
                settings.apply {
                    javaScriptEnabled = true
                    domStorageEnabled = true
                    databaseEnabled = true
                    setSupportZoom(true)
                    builtInZoomControls = false
                    displayZoomControls = false
                    loadWithOverviewMode = true
                    useWideViewPort = true
                    javaScriptCanOpenWindowsAutomatically = true
                    mediaPlaybackRequiresUserGesture = false
                    allowFileAccess = true
                    allowContentAccess = true

                    // Performance optimizations
                    cacheMode = android.webkit.WebSettings.LOAD_DEFAULT
                    setRenderPriority(android.webkit.WebSettings.RenderPriority.HIGH)
                    setEnableSmoothTransition(true)
                }

                webViewClient = object : WebViewClient() {
                    override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                        super.onPageStarted(view, url, favicon)
                        onPageStarted()
                    }

                    override fun onPageFinished(view: WebView?, url: String?) {
                        super.onPageFinished(view, url)
                        onPageFinished()
                    }

                    override fun onReceivedError(
                        view: WebView?,
                        request: WebResourceRequest?,
                        error: WebResourceError?
                    ) {
                        super.onReceivedError(view, request, error)
                        if (request?.isForMainFrame == true) {
                            onError(error?.description?.toString() ?: "Failed to load page")
                        }
                    }

                    override fun shouldOverrideUrlLoading(
                        view: WebView?,
                        request: WebResourceRequest?
                    ): Boolean {
                        // Allow navigation within the app
                        return false
                    }
                }

                webChromeClient = object : android.webkit.WebChromeClient() {
                    override fun onProgressChanged(view: WebView?, newProgress: Int) {
                        super.onProgressChanged(view, newProgress)
                        onProgressChanged(newProgress)
                    }
                }

                loadUrl(url)
                onWebViewCreated(this)
            }
        },
        modifier = Modifier.fillMaxSize(),
        update = { webView ->
            // Update WebView if needed
        }
    )
}

@Composable
fun ErrorScreen(
    errorMessage: String,
    onRetry: () -> Unit
) {
    val scale by rememberInfiniteTransition(label = "error").animateFloat(
        initialValue = 0.95f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "icon_scale"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(32.dp)
        ) {
            Icon(
                imageVector = Icons.Default.WifiOff,
                contentDescription = "Error",
                modifier = Modifier
                    .size(80.dp)
                    .scale(scale),
                tint = MaterialTheme.colorScheme.error
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Oops! Something went wrong",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = "Please check your internet connection and try again",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.7f),
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(32.dp))

            var buttonPressed by remember { mutableStateOf(false) }

            Button(
                onClick = {
                    buttonPressed = true
                    onRetry()
                },
                modifier = Modifier
                    .fillMaxWidth(0.6f)
                    .height(56.dp)
                    .scale(if (buttonPressed) 0.95f else 1f),
                shape = MaterialTheme.shapes.medium,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Text(
                    text = "Try Again",
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

@Composable
fun WhatsAppBusinessTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = Color(0xFF2563EB),  // Modern Blue
            onPrimary = Color.White,
            primaryContainer = Color(0xFFDBEAFE),
            secondary = Color(0xFF7C3AED),  // Purple accent
            background = Color(0xFFFAFAFA),
            surface = Color.White,
            surfaceVariant = Color(0xFFF5F5F5),
            error = Color(0xFFDC143C),
            onBackground = Color(0xFF1C1C1C),
            onSurface = Color(0xFF1C1C1C)
        ),
        typography = Typography(
            displayLarge = MaterialTheme.typography.displayLarge.copy(fontWeight = FontWeight.Bold),
            displayMedium = MaterialTheme.typography.displayMedium.copy(fontWeight = FontWeight.Bold),
            headlineLarge = MaterialTheme.typography.headlineLarge.copy(fontWeight = FontWeight.SemiBold),
            headlineMedium = MaterialTheme.typography.headlineMedium.copy(fontWeight = FontWeight.SemiBold),
            bodyLarge = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.Normal),
            bodyMedium = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Normal),
        ),
        shapes = Shapes(
            small = androidx.compose.foundation.shape.RoundedCornerShape(8.dp),
            medium = androidx.compose.foundation.shape.RoundedCornerShape(16.dp),
            large = androidx.compose.foundation.shape.RoundedCornerShape(24.dp)
        ),
        content = content
    )
}
