package ai.duckos.beelzebub;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.*;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.Locale;

final class ScannerEngine {
    static final long MAX_FILE_BYTES = 1024L * 1024 * 1024;
    static final int MAX_FILES = 100_000, MAX_DEPTH = 64;
    private static final byte[] EICAR = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*".getBytes(StandardCharsets.US_ASCII);
    private static final Set<String> SCRIPT_EXT = Set.of("ps1", "vbs", "js", "jse", "hta", "bat", "cmd", "sh", "py");
    private static final String[] TOKENS = {"downloadstring", "frombase64string", "invoke-expression", "iex(",
            "certutil -urlcache", "bitsadmin /transfer", "-windowstyle hidden", "powershell -enc",
            "encodedcommand", "/dev/tcp/", "curl | sh", "wget | sh"};

    interface Progress { void update(long files, long bytes, Path current); }
    private final SignatureCatalog signatures;
    ScannerEngine(SignatureCatalog signatures) { this.signatures = signatures; }

    ScanResult scan(Path selected, AtomicBoolean cancelled, Progress progress) throws IOException {
        if (selected == null || Files.isSymbolicLink(selected)) throw new IOException("Путь не должен быть символической ссылкой.");
        Path root = selected.toAbsolutePath().normalize();
        if (!Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Выберите существующую папку.");
        Instant start = Instant.now();
        List<ScanResult.Finding> findings = new ArrayList<>();
        long[] counts = new long[4];
        Files.walkFileTree(root, EnumSet.noneOf(FileVisitOption.class), MAX_DEPTH, new SimpleFileVisitor<>() {
            @Override public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) {
                if (cancelled.get()) return FileVisitResult.TERMINATE;
                if (Files.isSymbolicLink(dir) || dir.toAbsolutePath().normalize().equals(AppPaths.quarantine().toAbsolutePath().normalize()))
                    return FileVisitResult.SKIP_SUBTREE;
                return FileVisitResult.CONTINUE;
            }
            @Override public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                if (cancelled.get()) return FileVisitResult.TERMINATE;
                if (counts[0] >= MAX_FILES) { counts[2]++; return FileVisitResult.TERMINATE; }
                if (!attrs.isRegularFile() || Files.isSymbolicLink(file) || attrs.size() > MAX_FILE_BYTES) {
                    counts[2]++; return FileVisitResult.CONTINUE;
                }
                try {
                    ScanResult.Finding finding = scanFile(file);
                    counts[0]++; counts[1] += attrs.size();
                    if (finding != null) findings.add(finding);
                } catch (IOException | SecurityException e) { counts[3]++; }
                if (progress != null) progress.update(counts[0], counts[1], file);
                return FileVisitResult.CONTINUE;
            }
            @Override public FileVisitResult visitFileFailed(Path file, IOException e) {
                counts[3]++; return cancelled.get() ? FileVisitResult.TERMINATE : FileVisitResult.CONTINUE;
            }
        });
        return new ScanResult(root, counts[0], counts[1], counts[2], counts[3], cancelled.get(),
                Duration.between(start, Instant.now()), List.copyOf(findings));
    }

    ScanResult.Finding scanFile(Path file) throws IOException {
        if (file == null || Files.isSymbolicLink(file) || !Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS)) return null;
        long size = Files.size(file); if (size > MAX_FILE_BYTES) return null;
        MessageDigest digest;
        try { digest = MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        byte[] buffer = new byte[65536], tail = new byte[EICAR.length - 1];
        int tailLength = 0; boolean eicar = false;
        ByteArrayOutputStream sample = new ByteArrayOutputStream(65536);
        try (InputStream in = Files.newInputStream(file)) {
            int read;
            while ((read = in.read(buffer)) != -1) {
                digest.update(buffer, 0, read);
                if (!eicar) {
                    byte[] combined = new byte[tailLength + read];
                    System.arraycopy(tail, 0, combined, 0, tailLength);
                    System.arraycopy(buffer, 0, combined, tailLength, read);
                    eicar = contains(combined, EICAR);
                    tailLength = Math.min(tail.length, combined.length);
                    System.arraycopy(combined, combined.length - tailLength, tail, 0, tailLength);
                }
                if (sample.size() < 2 * 1024 * 1024)
                    sample.write(buffer, 0, Math.min(read, 2 * 1024 * 1024 - sample.size()));
            }
        }
        String hash = HexFormat.of().formatHex(digest.digest());
        SignatureCatalog.Indicator known = signatures.find(hash);
        if (known != null) return new ScanResult.Finding(file, hash, known.label(), known.severity(), "Совпадение SHA-256 с локальной базой", size);
        if (eicar) return new ScanResult.Finding(file, hash, "EICAR test file", "HIGH", "Обнаружена стандартная тестовая строка EICAR", size);
        String name = file.getFileName().toString(); int dot = name.lastIndexOf('.');
        String ext = dot < 0 ? "" : name.substring(dot + 1).toLowerCase(Locale.ROOT);
        if (SCRIPT_EXT.contains(ext)) {
            String text = sample.toString(StandardCharsets.ISO_8859_1).toLowerCase(Locale.ROOT);
            int matches = 0; String last = "";
            for (String token : TOKENS) if (text.contains(token)) { matches++; last = token; }
            if (matches >= 2) return new ScanResult.Finding(file, hash, "Suspicious script pattern", "SUSPICIOUS",
                    "Несколько рискованных команд в скрипте; совпадение: " + last, size);
        }
        return null;
    }

    private static boolean contains(byte[] data, byte[] pattern) {
        outer: for (int i = 0; i <= data.length - pattern.length; i++) {
            for (int j = 0; j < pattern.length; j++) if (data[i + j] != pattern[j]) continue outer;
            return true;
        }
        return false;
    }
}
