package io.github.apxkzmfh789.mes.alarm;

import java.math.BigDecimal;
import java.time.LocalDateTime;

// 경보 판정에 쓰는 예측 한 점 (설비 하나 기준)
public record ProbPoint(
        LocalDateTime dataTs,
        BigDecimal failureProb
) {
}