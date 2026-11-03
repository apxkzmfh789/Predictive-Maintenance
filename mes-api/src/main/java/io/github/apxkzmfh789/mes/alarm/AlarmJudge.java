package io.github.apxkzmfh789.mes.alarm;

import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;

@Component
public class AlarmJudge {

    // R5: 데이터 간격이 이보다 길면 연속 초기화
    private static final long MAX_GAP_MINUTES = 2;

    private final AlarmProperties properties;

    public AlarmJudge(AlarmProperties properties) {
        this.properties = properties;
    }

    /*
     * 설비 하나의 새 예측으로 경보 판정 (R5, R6, R7)
     * history       : 새 예측 바로 앞의 기존 예측. 연속 횟수를 이어 세기 위함 (시간순)
     * newPoints     : 이번에 새로 저장된 예측 (시간순)
     * hasOpenAlarm  : 이 설비에 OPEN·ACK 경보가 이미 있나
     * cooldownUntil : 재발생 금지가 끝나는 시각, 없으면 null
     */
    public JudgeResult judge(List<ProbPoint> history, List<ProbPoint> newPoints,
                             BigDecimal threshold, boolean hasOpenAlarm, LocalDateTime cooldownUntil) {
        Run run = new Run();

        // 이전 적재의 마지막 값들로 연속 상태만 이어 받음 (경보 판단은 안 함)
        for (ProbPoint point : history) {
            run.add(point, threshold);
        }

        boolean open = hasOpenAlarm;
        boolean created = false;
        LocalDateTime first = null;
        LocalDateTime last = null;
        BigDecimal max = null;
        int detected = 0;

        for (ProbPoint point : newPoints) {
            boolean above = run.add(point, threshold);
            if (!above) {
                continue;
            }

            // R6: 열린 경보가 있으면 새로 만들지 않고 갱신
            if (open) {
                detected++;
                last = point.dataTs();
                max = larger(max, point.failureProb());
                continue;
            }

            // R5: 연속 횟수가 모자라면 아직 아님
            if (run.count < properties.consecutiveCount()) {
                continue;
            }

            // R7: 재발생 금지 중이면 만들지 않음 (연속 횟수는 계속 셈)
            if (cooldownUntil != null && point.dataTs().isBefore(cooldownUntil)) {
                continue;
            }

            // 새 경보
            open = true;
            created = true;
            first = point.dataTs();
            last = point.dataTs();
            max = run.max;
            detected = run.count;
        }

        if (created) {
            return new JudgeResult(JudgeResult.Type.CREATE, first, last, max, detected);
        }
        if (detected > 0) {
            return new JudgeResult(JudgeResult.Type.UPDATE, null, last, max, detected);
        }
        return JudgeResult.none();
    }

    private static BigDecimal larger(BigDecimal a, BigDecimal b) {
        return (a == null || b.compareTo(a) > 0) ? b : a;
    }

    // 연속으로 임계값 이상인 구간의 상태 (판정하는 동안만 씀)
    private static class Run {
        LocalDateTime lastTs;
        int count;
        BigDecimal max;

        // 점 하나 반영, 임계값 이상이면 true
        boolean add(ProbPoint point, BigDecimal threshold) {
            // R5: 공백이 2분보다 길면 연속 끊김
            if (lastTs != null && Duration.between(lastTs, point.dataTs()).toMinutes() > MAX_GAP_MINUTES) {
                reset();
            }
            lastTs = point.dataTs();

            if (point.failureProb().compareTo(threshold) < 0) {
                reset();
                return false;
            }
            count++;
            max = larger(max, point.failureProb());
            return true;
        }

        void reset() {
            count = 0;
            max = null;
        }
    }
}