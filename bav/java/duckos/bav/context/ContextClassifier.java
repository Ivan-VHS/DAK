package duckos.bav.context;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

/** Bounded, local-only classifier for descriptive security context. */
public final class ContextClassifier {
    private static final long MAX_CATALOG_BYTES = 32 * 1024;
    private static final int MAX_CATALOG_LINES = 128;
    private static final int MAX_TEXT_CHARS = 1_048_576;
    private static final int MAX_TERM_CHARS = 160;

    public enum Category {
        WMD_CBRN("wmd_cbrn"),
        CHINESE_MILITARY_PLATFORMS("chinese_military_platforms"),
        AIR_DEFENSE_SYSTEMS("air_defense_systems");

        private final String id;

        Category(String id) {
            this.id = id;
        }

        public String id() {
            return id;
        }

        static Category fromId(String id) throws IOException {
            for (Category category : values()) {
                if (category.id.equals(id)) {
                    return category;
                }
            }
            throw new IOException("unknown defense-context category: " + id);
        }
    }

    public record ContextReport(Map<Category, List<String>> matches, int charactersScanned) {
        public ContextReport {
            Objects.requireNonNull(matches, "matches");
            EnumMap<Category, List<String>> copy = new EnumMap<>(Category.class);
            for (Map.Entry<Category, List<String>> entry : matches.entrySet()) {
                copy.put(entry.getKey(), List.copyOf(entry.getValue()));
            }
            matches = Collections.unmodifiableMap(copy);
        }

        public boolean hasSensitiveContext() {
            return !matches.isEmpty();
        }

        public int matchCount() {
            return matches.values().stream().mapToInt(List::size).sum();
        }
    }

    private final Map<Category, List<String>> terms;

    private ContextClassifier(Map<Category, List<String>> terms) {
        EnumMap<Category, List<String>> copy = new EnumMap<>(Category.class);
        terms.forEach((category, values) -> copy.put(category, List.copyOf(values)));
        this.terms = Collections.unmodifiableMap(copy);
    }

    public static ContextClassifier load(Path catalogPath) throws IOException {
        Objects.requireNonNull(catalogPath, "catalogPath");
        long size = Files.size(catalogPath);
        if (size > MAX_CATALOG_BYTES) {
            throw new IOException("defense-context catalog exceeds size limit");
        }

        EnumMap<Category, List<String>> loaded = new EnumMap<>(Category.class);
        for (Category category : Category.values()) {
            loaded.put(category, new ArrayList<>());
        }

        int lineCount = 0;
        int termCount = 0;
        try (BufferedReader reader = Files.newBufferedReader(catalogPath, StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                lineCount++;
                if (lineCount > MAX_CATALOG_LINES) {
                    throw new IOException("defense-context catalog exceeds line limit");
                }
                if (line.isBlank() || line.startsWith("#")) {
                    continue;
                }

                String[] fields = line.split("\\t", -1);
                if (fields.length != 2) {
                    throw new IOException("invalid catalog row at line " + lineCount);
                }

                Category category = Category.fromId(fields[0]);
                String term = normalize(fields[1]);
                if (term.isEmpty() || term.length() > MAX_TERM_CHARS || !isPlainTerm(term)) {
                    throw new IOException("invalid catalog term at line " + lineCount);
                }

                List<String> categoryTerms = loaded.get(category);
                if (categoryTerms.contains(term)) {
                    throw new IOException("duplicate catalog term at line " + lineCount);
                }
                categoryTerms.add(term);
                termCount++;
            }
        }

        if (termCount == 0 || loaded.values().stream().anyMatch(List::isEmpty)) {
            throw new IOException("catalog must define terms for all categories");
        }
        return new ContextClassifier(loaded);
    }

    public ContextReport classify(String content) {
        Objects.requireNonNull(content, "content");
        if (content.length() > MAX_TEXT_CHARS) {
            throw new IllegalArgumentException("content exceeds the 1 MiB character limit");
        }

        String normalized = normalize(content);
        Map<Category, List<String>> found = new LinkedHashMap<>();
        for (Category category : Category.values()) {
            List<String> categoryMatches = new ArrayList<>();
            for (String term : terms.get(category)) {
                if (containsWholePhrase(normalized, term)) {
                    categoryMatches.add(term);
                }
            }
            if (!categoryMatches.isEmpty()) {
                found.put(category, categoryMatches);
            }
        }
        return new ContextReport(found, content.length());
    }

    private static String normalize(String value) {
        String canonical = Normalizer.normalize(value, Normalizer.Form.NFKC)
                .toLowerCase(Locale.ROOT);
        return canonical.replaceAll("[\\p{Z}\\s]+", " ").trim();
    }

    private static boolean isPlainTerm(String value) {
        return value.codePoints().allMatch(codePoint ->
                Character.isLetterOrDigit(codePoint)
                        || codePoint == ' '
                        || codePoint == '-'
                        || codePoint == 0x2011);
    }

    private static boolean containsWholePhrase(String content, String term) {
        int from = 0;
        while (from <= content.length() - term.length()) {
            int index = content.indexOf(term, from);
            if (index < 0) {
                return false;
            }

            int end = index + term.length();
            boolean leftBoundary = index == 0
                    || !Character.isLetterOrDigit(content.codePointBefore(index));
            boolean rightBoundary = end == content.length()
                    || !Character.isLetterOrDigit(content.codePointAt(end));
            if (leftBoundary && rightBoundary) {
                return true;
            }
            from = index + 1;
        }
        return false;
    }
}
