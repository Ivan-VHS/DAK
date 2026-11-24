package ai.duckos.beelzebub;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.PosixFilePermissions;
import java.security.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;
import java.util.regex.Pattern;

final class AppPaths {
    private AppPaths() {}
    static Path dataDirectory() {
        String override = System.getProperty("duckos.beelzebub.data");
        if (override != null && !override.isBlank()) return Path.of(override).toAbsolutePath().normalize();
        String os = System.getProperty("os.name", "").toLowerCase(Locale.ROOT);
        if (os.contains("win")) {
            String base = System.getenv("LOCALAPPDATA");
            return Path.of(base == null || base.isBlank() ? System.getProperty("user.home") + "/AppData/Local" : base,
                    "DuckOS", "BeelzebubAV");
        }
        String base = System.getenv("XDG_DATA_HOME");
        return Path.of(base == null || base.isBlank() ? System.getProperty("user.home") + "/.local/share" : base,
                "duckos", "beelzebub-av");
    }
    static Path quarantine() { return dataDirectory().resolve("quarantine"); }
    static Path localSignatures() { return dataDirectory().resolve("signatures.local"); }
}

final class SignatureCatalog {
    private static final Pattern HASH = Pattern.compile("^[0-9a-fA-F]{64}$");
    private static final long MAX_FEED_BYTES = 32L * 1024 * 1024;
    private static final int MAX_INDICATORS = 250_000;
    private static final int MAX_LINE_CHARS = 512;
    record Indicator(String sha256, String label, String severity) {}
    private final Map<String, Indicator> indicators = new LinkedHashMap<>();

    SignatureCatalog() throws IOException {
        try (InputStream in = getClass().getResourceAsStream("/signatures.sha256")) {
            if (in != null) try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                read(reader);
            }
        }
        Path local = AppPaths.localSignatures();
        if (Files.isRegularFile(local, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(local)) {
            if (Files.size(local) > MAX_FEED_BYTES) throw new IOException("Локальная база индикаторов превышает 32 МиБ.");
            try (BufferedReader reader = Files.newBufferedReader(local, StandardCharsets.UTF_8)) { read(reader); }
        }
    }

    private void read(BufferedReader reader) throws IOException {
        String line; long total = 0;
        while ((line = reader.readLine()) != null) {
            total += line.length() + 1L;
            if (total > MAX_FEED_BYTES || line.length() > MAX_LINE_CHARS)
                throw new IOException("Локальная база индикаторов превышает допустимый размер.");
            String[] parts = line.strip().split("\\|", 3);
            if (parts.length != 3 || !HASH.matcher(parts[0]).matches()) continue;
            String severity = parts[1].toUpperCase(Locale.ROOT);
            if (!severity.equals("HIGH") && !severity.equals("CRITICAL")) continue;
            String hash = parts[0].toLowerCase(Locale.ROOT);
            if (!indicators.containsKey(hash) && indicators.size() >= MAX_INDICATORS)
                throw new IOException("В базе превышен лимит в 250 000 индикаторов.");
            indicators.put(hash, new Indicator(hash, parts[2].strip(), severity));
        }
    }
    Indicator find(String hash) { return indicators.get(hash.toLowerCase(Locale.ROOT)); }
    int size() { return indicators.size(); }

    synchronized int importFile(Path source) throws IOException {
        if (source == null || Files.isSymbolicLink(source) || !Files.isRegularFile(source, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Выберите обычный файл базы индикаторов, не символическую ссылку.");
        if (Files.size(source) > MAX_FEED_BYTES) throw new IOException("Файл базы индикаторов превышает 32 МиБ.");
        Map<String, Indicator> imported = new LinkedHashMap<>();
        try (BufferedReader reader = Files.newBufferedReader(source, StandardCharsets.UTF_8)) {
            String line; int n = 0; long total = 0;
            while ((line = reader.readLine()) != null) {
                n++; total += line.length() + 1L;
                if (total > MAX_FEED_BYTES || line.length() > MAX_LINE_CHARS) throw new IOException("Строка или размер базы индикаторов превышает лимит.");
                String value = line.strip();
                if (value.isEmpty() || value.startsWith("#")) continue;
                String[] parts = value.split("\\|", 3);
                if (parts.length != 3 || !HASH.matcher(parts[0]).matches())
                    throw new IOException("Некорректная строка " + n + ". Формат: SHA256|HIGH|label");
                String severity = parts[1].toUpperCase(Locale.ROOT);
                if (!severity.equals("HIGH") && !severity.equals("CRITICAL"))
                    throw new IOException("Недопустимый уровень в строке " + n + ": HIGH или CRITICAL.");
                String hash = parts[0].toLowerCase(Locale.ROOT);
                imported.put(hash, new Indicator(hash, parts[2].strip(), severity));
                if (imported.size() > MAX_INDICATORS) throw new IOException("В импортируемой базе больше 250 000 индикаторов.");
            }
        }
        if (imported.isEmpty()) throw new IOException("В файле нет корректных SHA-256 индикаторов.");
        Files.createDirectories(AppPaths.dataDirectory());
        Path destination = AppPaths.localSignatures();
        if (Files.isSymbolicLink(destination)) throw new IOException("Локальная база не должна быть символической ссылкой.");
        Map<String, Indicator> merged = new LinkedHashMap<>(indicators);
        long newHashes = imported.keySet().stream().filter(hash -> !merged.containsKey(hash)).count();
        if (merged.size() + newHashes > MAX_INDICATORS) throw new IOException("Объединённая база превышает 250 000 индикаторов.");
        merged.putAll(imported);
        Path temporary = Files.createTempFile(AppPaths.dataDirectory(), "signatures-", ".tmp");
        StringBuilder body = new StringBuilder("# DuckOS Beelzebub AV local SHA-256 indicators v1\n");
        merged.values().forEach(item -> body.append(item.sha256()).append('|').append(item.severity()).append('|')
                .append(item.label().replace('\n', ' ')).append('\n'));
        Files.writeString(temporary, body, StandardCharsets.UTF_8);
        try { Files.move(temporary, destination, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
        catch (IOException noAtomicMove) { Files.move(temporary, destination, StandardCopyOption.REPLACE_EXISTING); }
        indicators.clear(); indicators.putAll(merged);
        return imported.size();
    }
}

record ScanResult(Path target, long filesScanned, long bytesScanned, long skipped, long failures,
                  boolean cancelled, Duration duration, List<Finding> findings) {
    record Finding(Path path, String sha256, String name, String severity, String reason, long size) {}
    long threatsFound() { return findings.size(); }
}

final class QuarantineService {
    record Entry(String id, String name, String originalPath, String sha256, long size) {}
    QuarantineService() throws IOException {
        Files.createDirectories(AppPaths.quarantine());
        if (Files.isSymbolicLink(AppPaths.quarantine()) || !Files.isDirectory(AppPaths.quarantine(), LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Каталог карантина должен быть обычной директорией.");
        try { Files.setPosixFilePermissions(AppPaths.quarantine(), PosixFilePermissions.fromString("rwx------")); }
        catch (UnsupportedOperationException ignored) {}
    }

    synchronized Entry quarantine(Path selected) throws IOException {
        if (selected == null || Files.isSymbolicLink(selected) || !Files.isRegularFile(selected, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("В карантин можно переместить только обычный файл, не ссылку.");
        Path file = selected.toAbsolutePath().normalize();
        if (file.startsWith(AppPaths.quarantine().toAbsolutePath().normalize())) throw new IOException("Файл уже в карантине.");
        String hash = sha256(file), id = UUID.randomUUID().toString();
        Path stored = AppPaths.quarantine().resolve(id + ".blob");
        Path metadata = AppPaths.quarantine().resolve(id + ".properties");
        try { Files.move(file, stored, StandardCopyOption.ATOMIC_MOVE); }
        catch (IOException noAtomicMove) { Files.move(file, stored); }
        Properties p = new Properties();
        p.setProperty("id", id); p.setProperty("name", file.getFileName().toString());
        p.setProperty("original", file.toString()); p.setProperty("sha256", hash);
        try (OutputStream out = Files.newOutputStream(metadata)) { p.store(out, "Beelzebub AV quarantine metadata"); }
        return new Entry(id, file.getFileName().toString(), file.toString(), hash, Files.size(stored));
    }

    synchronized List<Entry> list() throws IOException {
        List<Entry> result = new ArrayList<>();
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(AppPaths.quarantine(), "*.properties")) {
            for (Path metadata : stream) {
                if (Files.isSymbolicLink(metadata) || !Files.isRegularFile(metadata, LinkOption.NOFOLLOW_LINKS)) continue;
                Properties p = new Properties();
                try (InputStream in = Files.newInputStream(metadata)) { p.load(in); }
                String id = p.getProperty("id", "");
                if (!id.matches("[0-9a-fA-F-]{36}")) continue;
                Path blob = AppPaths.quarantine().resolve(id + ".blob");
                if (Files.isSymbolicLink(blob) || !Files.isRegularFile(blob, LinkOption.NOFOLLOW_LINKS)) continue;
                result.add(new Entry(id, p.getProperty("name", "Unknown"), p.getProperty("original", ""),
                        p.getProperty("sha256", ""), Files.size(blob)));
            }
        }
        result.sort(Comparator.comparing(Entry::name, String.CASE_INSENSITIVE_ORDER));
        return result;
    }

    synchronized Path restore(String id) throws IOException {
        if (id == null || !id.matches("[0-9a-fA-F-]{36}")) throw new IOException("Некорректный идентификатор.");
        Path metadata = AppPaths.quarantine().resolve(id + ".properties");
        Path blob = AppPaths.quarantine().resolve(id + ".blob");
        if (Files.isSymbolicLink(metadata) || Files.isSymbolicLink(blob)
                || !Files.isRegularFile(metadata, LinkOption.NOFOLLOW_LINKS)
                || !Files.isRegularFile(blob, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Объект карантина не найден.");
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(metadata)) { p.load(in); }
        Path destination = Path.of(p.getProperty("original", "")).toAbsolutePath().normalize();
        if (destination.getParent() == null || destination.getFileName() == null) throw new IOException("Некорректный исходный путь.");
        Path current = destination.getParent().getRoot();
        for (Path part : destination.getParent()) {
            current = current == null ? part : current.resolve(part);
            if (Files.exists(current, LinkOption.NOFOLLOW_LINKS) && Files.isSymbolicLink(current))
                throw new IOException("Восстановление остановлено: родитель содержит символическую ссылку.");
        }
        Files.createDirectories(destination.getParent());
        if (Files.exists(destination, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Исходный путь занят. Перезапись запрещена.");
        if (!p.getProperty("sha256", "").equalsIgnoreCase(sha256(blob)))
            throw new IOException("Хеш карантинного объекта не совпадает с метаданными.");
        try { Files.move(blob, destination, StandardCopyOption.ATOMIC_MOVE); }
        catch (IOException noAtomicMove) { Files.move(blob, destination); }
        Files.delete(metadata);
        return destination;
    }

    static String sha256(Path file) throws IOException {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (InputStream in = Files.newInputStream(file)) {
                byte[] buffer = new byte[65536]; int read;
                while ((read = in.read(buffer)) != -1) digest.update(buffer, 0, read);
            }
            return HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}

final class ScanWatcher implements AutoCloseable {
    private static final int MAX_WATCHED_DIRECTORIES = 4096;
    private final ScannerEngine engine;
    private final Consumer<ScanResult.Finding> findings;
    private volatile boolean running;
    private WatchService watch;
    private Thread thread;
    ScanWatcher(ScannerEngine engine, Consumer<ScanResult.Finding> findings) { this.engine = engine; this.findings = findings; }

    synchronized void start(Path selected) throws IOException {
        if (running) throw new IOException("Наблюдение уже запущено.");
        if (selected == null || Files.isSymbolicLink(selected) || !Files.isDirectory(selected, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Выберите существующую папку, не символическую ссылку.");
        watch = FileSystems.getDefault().newWatchService();
        Map<WatchKey, Path> keys = new HashMap<>();
        try (var paths = Files.walk(selected, ScannerEngine.MAX_DEPTH)) {
            paths.filter(p -> Files.isDirectory(p, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(p))
                    .limit(MAX_WATCHED_DIRECTORIES).forEach(p -> register(p, keys));
        }
        running = true;
        thread = new Thread(() -> loop(keys), "beelzebub-live-guard"); thread.setDaemon(true); thread.start();
    }
    private void register(Path path, Map<WatchKey, Path> keys) {
        if (keys.size() >= MAX_WATCHED_DIRECTORIES || keys.containsValue(path)) return;
        try { keys.put(path.register(watch, StandardWatchEventKinds.ENTRY_CREATE, StandardWatchEventKinds.ENTRY_MODIFY), path); }
        catch (IOException ignored) {}
    }
    private void loop(Map<WatchKey, Path> keys) {
        while (running) {
            WatchKey key;
            try { key = watch.take(); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); break; }
            catch (ClosedWatchServiceException e) { break; }
            Path parent = keys.get(key);
            if (parent != null) for (WatchEvent<?> event : key.pollEvents()) {
                if (event.kind() == StandardWatchEventKinds.OVERFLOW) continue;
                Path changed = parent.resolve((Path) event.context());
                try {
                    if (Files.isSymbolicLink(changed)) continue;
                    if (Files.isDirectory(changed, LinkOption.NOFOLLOW_LINKS) && event.kind() == StandardWatchEventKinds.ENTRY_CREATE) {
                        try (var paths = Files.walk(changed, ScannerEngine.MAX_DEPTH)) {
                            paths.filter(p -> Files.isDirectory(p, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(p)).limit(MAX_WATCHED_DIRECTORIES).forEach(p -> register(p, keys));
                        }
                    } else if (Files.isRegularFile(changed, LinkOption.NOFOLLOW_LINKS)) {
                        ScanResult.Finding finding = engine.scanFile(changed);
                        if (finding != null) findings.accept(finding);
                    }
                } catch (IOException | SecurityException ignored) {}
            }
            if (!key.reset()) keys.remove(key);
        }
    }
    boolean isRunning() { return running; }
    @Override public synchronized void close() {
        running = false;
        if (watch != null) try { watch.close(); } catch (IOException ignored) {}
        if (thread != null) thread.interrupt();
        watch = null; thread = null;
    }
}
