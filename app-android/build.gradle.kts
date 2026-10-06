// Oberste Build-Datei: hier werden nur die Plugin-Versionen festgelegt.
// Die eigentliche App-Konfiguration steht in app/build.gradle.kts.
plugins {
    alias(libs.plugins.android.application) apply false
    // AGP 9 bringt Kotlin schon eingebaut mit. Diese Zeile hebt nur die
    // Kotlin-Version auf den Stand aus libs.versions.toml an.
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.ksp) apply false
}
