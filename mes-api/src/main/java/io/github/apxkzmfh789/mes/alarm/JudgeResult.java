package io.github.apxkzmfh789.mes.alarm;

import java.math.BigDecimal;
import java.time.LocalDateTime;

// 설비 하나의 판정 결과
public record JudgeResult(
        Type type,
        LocalDateTime firstDetectedTs,  // CREATE일 때 경보 생성 시각
        LocalDateTime lastDetectedTs,   // 마지막으로 임계값을 넘은 시각
        BigDecimal maxProb,             // 이번 판정에서 본 최고 확률
        int detectCount                 // CREATE면 전체 감지 횟수, UPDATE면 이번에 더해질 횟수
) {

    public enum Type { NONE, UPDATE, CREATE }

    public static JudgeResult none() {
        return new JudgeResult(Type.NONE, null, null, null, 0);
    }
}