package com.whatsapp.business.automation

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class WhatsAppApp : Application() {

    override fun onCreate() {
        super.onCreate()

        // Create notification channels for Android O+
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val notificationManager = getSystemService(NotificationManager::class.java)

            // Messages channel
            val messagesChannel = NotificationChannel(
                CHANNEL_MESSAGES,
                "Messages",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Notifications for new messages"
                enableVibration(true)
            }

            // Campaigns channel
            val campaignsChannel = NotificationChannel(
                CHANNEL_CAMPAIGNS,
                "Campaigns",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Notifications for campaign updates"
            }

            // General channel
            val generalChannel = NotificationChannel(
                CHANNEL_GENERAL,
                "General",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "General notifications"
            }

            notificationManager.createNotificationChannels(
                listOf(messagesChannel, campaignsChannel, generalChannel)
            )
        }
    }

    companion object {
        const val CHANNEL_MESSAGES = "messages_channel"
        const val CHANNEL_CAMPAIGNS = "campaigns_channel"
        const val CHANNEL_GENERAL = "general_channel"
    }
}
