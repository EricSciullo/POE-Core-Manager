# POE-Core-Manager

This is based on https://github.com/Kapps/PoEUncrasher

Tool for avoiding PC freezes with Path of Exile 2 on certain Windows versions and processors. It seems this mostly impacts people with AMD X3D processors on Windows 24H2 specifically.



This tool detects when your game starts up or starts a loading screen and changes the process affinity to not use the first two cores. They are enabled again once you're actually in the game. People have been doing this manually but doing so will mean you lose performance unless you re-enable the cores after every loading screen.

# Using with Steam

If you're using Steam, you can set this to auto-start when you start the game.
1. Right click Path of Exile 2 in your Steam library
2. Click "Properties..."
3. Paste `cmd /c start "Path of Exile Core Manager" "C:\Users\you\Desktop\poe_core_manager.exe" && %command%` changing the path to the executable
