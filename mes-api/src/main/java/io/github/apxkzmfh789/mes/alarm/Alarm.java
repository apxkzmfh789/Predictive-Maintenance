package io.github.apxkzmfh789.mes.alarm;

import java.math.BigDecimal;
import java.time.LocalDateTime;

// 경보 한 행 + 화면 표시용 설비 코드·이름 (SELECT 컬럼 순서와 같음)
public record Alarm(
        Integer alarmId,
        Integer equipmentId,
        String equipmentCode,
        String equipmentName,
        Integer batchId,
        String status,
        LocalDateTime firstDetectedTs,
        LocalDateTime lastDetectedTs,
        BigDecimal maxProb,
        Integer detectCount,
        LocalDateTime createdAt,
        LocalDateTime ackedAt,
        String ackedBy,
        LocalDateTime closedAt,
        String closedBy,
        String closeReason,
        String closeMemo,
        LocalDateTime closeDataTs
) {
}