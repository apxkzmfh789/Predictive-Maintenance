package io.github.apxkzmfh789.mes.prediction;

import java.math.BigDecimal;
import java.time.LocalDateTime;

// prediction 테이블 한 행, SELECT 컬럼 순서와 필드 순서를 맞춤
public record Prediction(
        Integer equipmentId,
        LocalDateTime dataTs,
        Integer batchId,
        BigDecimal failureProb
) {
}