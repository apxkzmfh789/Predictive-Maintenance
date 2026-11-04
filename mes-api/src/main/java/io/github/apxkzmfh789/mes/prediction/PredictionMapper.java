package io.github.apxkzmfh789.mes.prediction;

import io.github.apxkzmfh789.mes.alarm.ProbPoint;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface PredictionMapper {

    // 같은 (설비, 시각)이 없을 때만 저장, 1이면 저장 0이면 중복 (R2)
    int insertIfAbsent(@Param("equipmentId") int equipmentId,
                       @Param("dataTs") LocalDateTime dataTs,
                       @Param("batchId") int batchId,
                       @Param("failureProb") BigDecimal failureProb);

    List<ProbPoint> findRecentBefore(@Param("equipmentId") int equipmentId,
                                     @Param("beforeTs") LocalDateTime beforeTs,
                                     @Param("limit") int limit);

    // 설비 하나의 기간 예측, 시간순 (from 이상, to 미만)
    List<Prediction> findByRange(@Param("equipmentId") int equipmentId,
                                 @Param("from") LocalDateTime from,
                                 @Param("to") LocalDateTime to);
}