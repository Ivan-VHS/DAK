# Beelzebub AV for DuckOS

Beelzebub AV is a standalone Java 17+ user-space file scanner with a native Swing interface designed in the DuckOS Mora visual language (black, white and duck yellow). It is a new DuckOS application and is not a port of the similarly named Go honeypot/deception runtime.

## Build and run

~~~sh
./build.sh
java -jar build/beelzebub-av.jar
java -jar build/beelzebub-av.jar --scan "$HOME/Downloads"
./test.sh
~~~

DuckOS integration:

~~~sh
duckos beelzebub status
duckos beelzebub gui
duckos beelzebub scan "$HOME/Downloads"
~~~

The native workbench builds the JAR on first launch. It invokes javac and jar with a fixed argument vector, shell=False, and bounded timeouts. No third-party Java runtime libraries are required.

## Detection and response scope

- Recursive on-demand scan of a user-selected directory.
- Streaming SHA-256 hashing and matching against built-in/local indicators.
- Detection of the standard EICAR test string, including when it crosses an input-buffer boundary.
- Conservative multi-token heuristics for suspicious commands in selected script extensions. Heuristic findings are labelled SUSPICIOUS, not confirmed malware.
- Optional monitoring of explicitly selected folders through Java WatchService.
- Explicit user-approved quarantine, SHA-256 verification at restore, collision-safe restoration, and no automatic deletion.
- Import of a local indicator list in SHA256|HIGH|label or SHA256|CRITICAL|label format.

The built-in SHA-256 list is intentionally empty: this source repository does not redistribute a maintained malware corpus. Import indicator lists only from a trusted source. Initial local imports are not signed or authenticated by the application.

## Data and boundaries

Data is stored under %LOCALAPPDATA%/DuckOS/BeelzebubAV on Windows, or $XDG_DATA_HOME/duckos/beelzebub-av (default ~/.local/share/duckos/beelzebub-av) on Linux/macOS.

This is a functional user-space scanner, not a kernel antivirus. WatchService observes selected directories and can miss transient events or writes outside those trees. The initial release does not provide a kernel minifilter, process-execution blocking, memory/network/boot scanning, automatic disinfection, automatic signature updates, publisher trust verdicts, or a malware-prevention guarantee. Findings are evidence for review; quarantine is a reversible move, not disinfection.

## Verification

Run ./test.sh with JDK 17 or newer. The self-test covers EICAR matching, local SHA-256 import, script heuristics, symlink rejection, quarantine, restoration, and refusal to overwrite an existing destination.
