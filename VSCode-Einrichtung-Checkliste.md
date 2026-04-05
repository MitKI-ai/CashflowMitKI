# VS Code Einrichtung – Anfänger-Checkliste

## 1. Installation
- [x ] VS Code von [code.visualstudio.com](https://code.visualstudio.com) herunterladen & installieren
- [ ] Beim Setup: "Zu PATH hinzufügen" aktivieren (Windows)

## 2. Grundeinstellungen
- [ x] Sprache einstellen: Extension **"German Language Pack"** installieren
- [ x] Theme wählen: `Ctrl+K, Ctrl+T` → z.B. *Dark Modern* oder *One Dark Pro*
- [ x] Schriftgröße anpassen: `Ctrl+,` → `Editor: Font Size` (Empfehlung: 14–16)
- [ x] Auto-Save aktivieren: `Ctrl+,` → `Files: Auto Save` → `afterDelay`

## 3. Wichtige Extensions
- [x ] **Prettier** – automatische Code-Formatierung
- [ ] **ESLint** – JavaScript/TypeScript Fehlerprüfung
- [ ] **Live Server** – lokaler Webserver mit Auto-Reload (für HTML/CSS/JS)
- [ ] **GitLens** – erweiterte Git-Integration
- [ ] **IntelliCode** – KI-gestützte Autovervollständigung

## 4. Git einrichten
- [ ] Git installieren: [git-scm.com](https://git-scm.com)
- [ ] Terminal: `git config --global user.name "Dein Name"`
- [ ] Terminal: `git config --global user.email "deine@email.de"`
- [ ] VS Code erkennt Git automatisch – prüfen via Source Control Seitenleiste (`Ctrl+Shift+G`)

## 5. Terminal & Workflow
- [ ] Integriertes Terminal öffnen: `` Ctrl+` ``
- [ ] Standard-Shell setzen (PowerShell, Git Bash, etc.)
- [ ] Projektordner öffnen: `Ctrl+K, Ctrl+O`
            
## 6. Die wichtigsten Shortcuts lernen (Deutsche Tastatur)

### Allgemein
| Aktion | Shortcut |
|---|---|
| Befehlspalette | `Strg+Shift+P` |
| Datei suchen | `Strg+P` |
| Einstellungen | `Strg+,` |
| Terminal ein/aus | `` Strg+Ö `` |
| Seitenleiste ein/aus | `Strg+B` |
| Neues Fenster | `Strg+Shift+N` |
| Datei schließen | `Strg+W` |
| Alle Dateien schließen | `Strg+K, Strg+W` |

### Bearbeiten
| Aktion | Shortcut |
|---|---|
| Zeile duplizieren | `Shift+Alt+↓` |
| Zeile verschieben | `Alt+↑ / Alt+↓` |
| Zeile löschen | `Strg+Shift+K` |
| Mehrzeilenauswahl | `Alt+Klick` |
| Nächstes Vorkommen markieren | `Strg+D` |
| Alle Vorkommen markieren | `Strg+Shift+L` |
| Alles formatieren | `Shift+Alt+F` |
| Rückgängig | `Strg+Z` |
| Wiederherstellen | `Strg+Ü` |
| Kommentar umschalten | `Strg+#` |
| Einrücken / Ausrücken | `Tab / Shift+Tab` |

### Navigation
| Aktion | Shortcut |
|---|---|
| Zur Definition springen | `F12` |
| Zurück navigieren | `Alt+←` |
| Suchen | `Strg+F` |
| Suchen & Ersetzen | `Strg+H` |
| In Dateien suchen | `Strg+Shift+F` |
| Zwischen Tabs wechseln | `Strg+Tab` |
| Zur Zeile springen | `Strg+G` |

### Git (Source Control)
| Aktion | Shortcut |
|---|---|
| Source Control öffnen | `Strg+Shift+G` |
| Git: Änderungen anzeigen | In Source Control Seitenleiste |

## 7. Optionale Extras
- [ ] **Settings Sync** aktivieren (über GitHub-Account) – Einstellungen geräteübergreifend sichern
- [ ] Icon-Theme installieren (z.B. *Material Icon Theme*)
- [ ] Sprachspezifische Extensions je nach Bedarf (Python, C#, Java, etc.)

---

**Tipp:** Starte klein – installiere nur Extensions, die du wirklich brauchst. Zu viele Extensions verlangsamen VS Code.
