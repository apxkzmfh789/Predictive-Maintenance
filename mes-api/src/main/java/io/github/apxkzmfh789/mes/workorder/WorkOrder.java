package io.github.apxkzmfh789.mes.workorder;

import java.time.LocalDateTime;

// 작업지시 한 행 + 화면 표시용 설비 정보 (SELECT 컬럼 순서와 같음)
public record WorkOrder(
        Integer workOrderId,
        Integer alarmId,
        Integer equipmentId,
        String equipmentCode,
        String equipmentName,
        String status,
        String workType,
        String assignee,
        String instruction,
        String resultCode,
        String actionNote,
        String createdBy,
        LocalDateTime createdAt,
        LocalDateTime startedAt,
        LocalDateTime completedAt,
        LocalDateTime canceledAt
) {
}