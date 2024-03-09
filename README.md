# Discord Web Tray

Make browser Discord feel more native by giving it a tray icon.

Inspired by the tray button from [WebCord](https://github.com/SpacingBat3/WebCord).

## Features

- Cross-platform
- Lightweight
- Automatically updating icon and tooltip
- "Toggle" - Focus the tab
- "Quit" - Close the tab

## Installation

1. Make sure you have Git, Python (at least v3.5), and Tampermonkey installed

   https://www.python.org/downloads/

   https://git-scm.com/downloads

   https://www.tampermonkey.net/

2. Clone the repository

   ```sh
   git clone https://github.com/e9x/discord-web-tray
   cd discord-web-tray
   ```

3. Install server dependencies

   ```sh
   pip install -r ./requirements.txt
   ```

4. Install the helper script

   Make sure Tampermonkey is installed, and open this link in your browser: https://raw.githubusercontent.com/e9x/discord-web-tray/master/helper.user.js

5. Start the server

   The tray icon will only appear once you open a Discord tab.

   ```sh
   python3 ./server.py
   ```

   On Linux, you can just execute server.py:

   ```sh
   ./server.py
   ```

6. Open Discord in your browser

## Troubleshooting

### Server runs but icon doesn't show up

- The tray icon will only appear once you open a Discord tab.
- Make sure the helper script is installed and the server is running.
- If you're using a proxy, configure it to ignore `127.0.0.1`.

## Extras

### Changing the port

You can change the port by changing `serverPort` in `server.py` and in the Tampermonkey script.

### Allow multiple trays

This is disabled by default and you can enable it by changing `allowMultipleTrays` in `server.py` from `False` to `True`
