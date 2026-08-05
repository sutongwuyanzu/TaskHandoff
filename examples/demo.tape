# VHS tape — real terminal recording (optional)
# https://github.com/charmbracelet/vhs
# Requires: vhs + ffmpeg
# Run: vhs examples/demo.tape

Output assets/terminal-demo.gif
Set FontSize 15
Set Width 1000
Set Height 560
Set Theme "Catppuccin Mocha"
Set Padding 12
Set TypingSpeed 35ms

Hide
Type "export PS1='$ '"
Enter
# create demo dir
Type "rm -rf /tmp/th-demo && mkdir -p /tmp/th-demo && cd /tmp/th-demo && echo \"print(1)\" > app.py"
Enter
Sleep 500ms
Show

Type "handoff --version"
Enter
Sleep 800ms

Type "handoff init --root ."
Enter
Sleep 1000ms

Type "handoff save --root . --auto --goal 'Ship JWT auth' --next 'Finish refresh' --next 'Add tests' --next 'Docs'"
Enter
Sleep 1400ms

Type "handoff recall --root . --brief"
Enter
Sleep 1600ms

Type "handoff doctor --root ."
Enter
Sleep 2000ms
