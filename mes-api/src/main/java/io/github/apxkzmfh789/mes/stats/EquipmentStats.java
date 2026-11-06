package io.github.apxkzmfh789.mes.stats;

import java.math.BigDecimal;

// 설비별 집계 (SELECT 컬럼 순서와 같음). 분모가 0이면 비율·평균은 null
public record EquipmentStats(
        Integer equipmentId,
        String equipmentCode,
        String equipmentName,
        Integer alarmCount,
        Integer closedCount,
        Integer falseAlarmCount,
        BigDecimal falseAlarmRate,
        Integer doneCount,
        Integer noIssueCount,
        BigDecimal noIssueRate,
        BigDecimal avgAckMinutes,
        BigDecimal avgActionMinutes,
        BigDecimal downtimeMinutes
) {
}