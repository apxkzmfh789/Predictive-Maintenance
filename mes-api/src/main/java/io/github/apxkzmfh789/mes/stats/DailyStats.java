package io.github.apxkzmfh789.mes.stats;

import java.time.LocalDate;

// 날짜별 건수. 아무 일도 없던 날은 행이 없음
public record DailyStats(
        LocalDate statDate,
        Integer alarmCount,
        Integer falseAlarmCount,
        Integer workOrderCount,
        Integer workOrderDoneCount
) {
}