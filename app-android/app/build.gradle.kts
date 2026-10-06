import java.util.Properties

// Build-Datei des App-Moduls
plugins {
    alias(libs.plugins.android.application)
    // Kein "kotlin-android" nötig: AGP 9 hat Kotlin eingebaut.
    alias(libs.plugins.kotlin.compose)        // Compose-Compiler
    alias(libs.plugins.kotlin.serialization)  // JSON für Supabase
    alias(libs.plugins.ksp)                   // Code-Generator für Room
}

// --- Geheime Werte aus local.properties lesen (Datei ist NICHT im Git!) ---
val localProps = Properties().apply {
    val datei = rootProject.file("local.properties")
    if (datei.exists()) datei.inputStream().use { load(it) }
}
fun geheim(name: String): String = localProps.getProperty(name, "").trim()

android {
    namespace = "de.hydrodesk.app"
    compileSdk = 37

    defaultConfig {
        applicationId = "de.hydrodesk.app"
        minSdk = 26          // Android 8.0
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"

        // Werden zu BuildConfig.SUPABASE_URL und BuildConfig.SUPABASE_ANON_KEY
        buildConfigField("String", "SUPABASE_URL", "\"${geheim("SUPABASE_URL")}\"")
        buildConfigField("String", "SUPABASE_ANON_KEY", "\"${geheim("SUPABASE_ANON_KEY")}\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

// Room: Datenbank-Schema als JSON ablegen (hilft bei späteren Migrationen)
ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.navigation.compose)

    // Compose
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons.core)
    debugImplementation(libs.androidx.compose.ui.tooling)

    // Room
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)

    // WorkManager
    implementation(libs.androidx.work.runtime.ktx)

    // Supabase + Ktor (HTTP-Client)
    implementation(platform(libs.supabase.bom))
    implementation(libs.supabase.auth)
    implementation(libs.supabase.postgrest)
    implementation(libs.ktor.client.okhttp)
    implementation(libs.kotlinx.serialization.json)

    // Unit-Tests (laufen auf dem PC, ohne Handy)
    testImplementation(libs.junit)
}
