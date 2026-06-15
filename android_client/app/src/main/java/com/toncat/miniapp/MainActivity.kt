package com.toncat.miniapp

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Инициализация WebView как основного view для Activity
        webView = WebView(this)
        setContentView(webView)

        // Настройки WebView для работы React-приложения, видео и скриптов
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false // Для автоматического воспроизведения видео
            setSupportZoom(false)
            displayZoomControls = false
            loadWithOverviewMode = true
            useWideViewPort = true
            cacheMode = WebSettings.LOAD_DEFAULT
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        }

        // Чтобы ссылки открывались внутри приложения, а не во внешнем браузере
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                if (url != null && url.startsWith("tc://")) {
                    // Обработка TON Connect deeplinks, если нужно
                    // val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    // startActivity(intent)
                    // return true
                }
                return false
            }
        }

        // WebChromeClient необходим для поддержки видео и сложных JS alert-ов
        webView.webChromeClient = WebChromeClient()

        // Загрузка URL вашего Mini App.
        // Замените этот URL на реальный адрес, где хостится ваш React frontend
        val miniAppUrl = "http://192.168.1.151:5173" // или "https://your-domain.com"
        webView.loadUrl(miniAppUrl)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
