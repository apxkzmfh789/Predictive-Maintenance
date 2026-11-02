package io.github.apxkzmfh789.mes.prediction;

import java.math.BigDecimal;
import java.time.LocalDateTime;

// 적재 결과 요약 (응답)
public record ImportResult(
        Integer batchId,            // 적재 이력 ID, 3단계부터
        int rowsRead,               // 구간 안에서 읽은 행
        int rowsInserted,           // 새로 저장한 행, 3단계부터
        int rowsSkipped,            // 건너뛴 행, 3단계부터
        int alarmsCreated,          // 새로 생긴 경보, 5단계부터
        LocalDateTime dataFrom,     // 읽은 데이터의 첫 시각 (KST)
        LocalDateTime dataTo,       // 읽은 데이터의 마지막 시각 (KST)
        BigDecimal modelThreshold,  // metrics.json 임계값
        BigDecimal appliedThreshold // 실제 적용 임계값 (R1)
) {
}