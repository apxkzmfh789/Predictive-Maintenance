package io.github.apxkzmfh789.mes.prediction;

import java.math.BigDecimal;
import java.time.LocalDateTime;

// CSV 한 줄을 읽어 정리한 값 (시각은 KST)
public record PredictionRow(
        String equipmentCode,
        LocalDateTime dataTs,
        BigDecimal failureProb
) {
}
