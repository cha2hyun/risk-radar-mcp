# macOS LaunchAgent

Example LaunchAgent for running `risk-radar-mcp` after login.

Save as:

```txt
~/Library/LaunchAgents/io.github.YOUR_USER.risk-radar-mcp.plist
```

Adjust paths before use.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>io.github.YOUR_USER.risk-radar-mcp</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/YOUR_USER/.local/bin/uv</string>
    <string>run</string>
    <string>risk-radar-mcp</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/YOUR_USER/risk-radar-mcp</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>RISK_RADAR_HOST</key>
    <string>127.0.0.1</string>
    <key>RISK_RADAR_PORT</key>
    <string>8765</string>
  </dict>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/Users/YOUR_USER/risk-radar-mcp/logs/launchd.log</string>

  <key>StandardErrorPath</key>
  <string>/Users/YOUR_USER/risk-radar-mcp/logs/launchd.error.log</string>
</dict>
</plist>
```

Load:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/io.github.YOUR_USER.risk-radar-mcp.plist
```

Check:

```bash
launchctl print gui/$(id -u)/io.github.YOUR_USER.risk-radar-mcp
```

Restart:

```bash
launchctl kickstart -k gui/$(id -u)/io.github.YOUR_USER.risk-radar-mcp
```
