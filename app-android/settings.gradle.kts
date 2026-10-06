// Einstellungen für den Gradle-Build: woher kommen Plugins und Bibliotheken?
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    // Bibliotheken nur aus diesen Quellen laden (nicht pro Modul festlegen)
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "HydroDesk"
include(":app")
