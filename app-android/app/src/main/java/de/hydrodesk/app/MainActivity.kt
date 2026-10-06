package de.hydrodesk.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import de.hydrodesk.app.ui.HydroDeskRoot
import de.hydrodesk.app.ui.theme.HydroDeskTheme

/** Die einzige Activity: zeigt die Compose-Oberfläche an. */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            HydroDeskTheme {
                HydroDeskRoot()
            }
        }
    }
}
