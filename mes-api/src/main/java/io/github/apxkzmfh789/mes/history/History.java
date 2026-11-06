package io.github.apxkzmfh789.mes.history;

import java.time.LocalDateTime;

// 상태 변경 이력 한 행 (SELECT 컬럼 순서와 같음)
public record History(
        Integer historyId,
        String targetType,
        Integer targetId,
        String fromStatus,
        String toStatus,
        String changedBy,
        LocalDateTime changedAt,
        String memo
) {
}