package io.github.apxkzmfh789.mes.alarm;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.math.BigDecimal;

// application.yaml의 mes.alarm.* 값을 받는 그릇
@ConfigurationProperties(prefix = "mes.alarm")
public record AlarmProperties(
        int consecutiveCount,           // R5 연속 횟수
        int cooldownMinutes,            // R7 재발생 금지 시간
        BigDecimal thresholdOverride    // R1 임계값 재정의, 없으면 null
) {
}

