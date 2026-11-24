package duckos.bav.context;

import java.nio.file.Path;

public final class ContextClassifierSelfTest {
    private ContextClassifierSelfTest() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException(
                    "usage: ContextClassifierSelfTest <catalog.tsv>");
        }

        ContextClassifier classifier = ContextClassifier.load(Path.of(args[0]));
        ContextClassifier.ContextReport report = classifier.classify(
                "Справочный материал: Ядерное оружие; Китайские танки; "
                        + "мобильный комплекс ПВО."
        );

        require(report.hasSensitiveContext(), "expected context tags");
        require(report.matches().containsKey(ContextClassifier.Category.WMD_CBRN),
                "missing WMD tag");
        require(report.matches().containsKey(
                        ContextClassifier.Category.CHINESE_MILITARY_PLATFORMS),
                "missing platform tag");
        require(report.matches().containsKey(
                        ContextClassifier.Category.AIR_DEFENSE_SYSTEMS),
                "missing air-defense tag");
        require(report.matchCount() == 3, "unexpected number of matches");

        ContextClassifier.ContextReport clean = classifier.classify(
                "обычная документация о сборке приложения");
        require(!clean.hasSensitiveContext(), "unexpected context match");
        require(!classifier.classify("антиЯдерное оружие").hasSensitiveContext(),
                "substring must not match a complete phrase");

        boolean bounded = false;
        try {
            classifier.classify("x".repeat(1_048_577));
        } catch (IllegalArgumentException expected) {
            bounded = true;
        }
        require(bounded, "oversized input must be rejected");
        System.out.println("BAV context classifier self-test passed");
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
