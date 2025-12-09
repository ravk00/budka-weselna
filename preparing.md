# Install required packages

```
sudo apt update
sudo apt install python3-pip python3-venv ffmpeg libxcb-cursor0 -y

# Tworzymy wirtualne środowisko dla porządku (opcjonalne, ale zalecane)
mkdir -p ~/videobooth
cd ~/videobooth
python3 -m venv venv
source venv/bin/activate

# Instalujemy biblioteki Pythona
pip install PyQt6
```

Create 'main.py'

# Run for test
```
python3 main.py
```
> To exit use 'Ctrl + Shift + Q' shortcut

# Create autostart file

```
mkdir -p ~/.config/autostart
nano ~/.config/autostart/videobooth.desktop
```
## Paste code
```
[Desktop Entry]
Type=Application
Name=Video Booth
Exec=/bin/bash -c "source /home/USERNAME/videobooth/venv/bin/activate && python3 /home/USERNAME/videobooth/main.py"
X-GNOME-Autostart-enabled=true
```

> Change 'USERNAME' for your user name


# Ukrywanie elementów systemu (GNOME)
Ubuntu 22.04 używa GNOME. Aby zrobić "bieda-kiosk", musimy wyłączyć dock, górny pasek i wygaszacz ekranu.

W ustawieniach systemowych (Settings):

Power: Screen Blank -> Never.

Notifications: Do Not Disturb -> ON.

W terminalu (aby ukryć Dock i wyłączyć gesty):

```
# Wyłącz wygaszacz ekranu
gsettings set org.gnome.desktop.session idle-delay 0

# Auto-ukrywanie docka (aplikacja fullscreen i tak go przykryje, ale dla pewności)
gsettings set org.gnome.shell.extensions.dash-to-dock autohide true
gsettings set org.gnome.shell.extensions.dash-to-dock dock-fixed false
gsettings set org.gnome.shell.extensions.dash-to-dock intellihide false
```
