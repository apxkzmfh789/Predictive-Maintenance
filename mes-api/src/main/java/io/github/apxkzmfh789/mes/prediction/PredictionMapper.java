package io.github.apxkzmfh789.mes.prediction;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Mapper
public interface PredictionMapper {

    // 같은 (설비, 시각)이 없을 때만 저장, 1이면 저장 0이면 중복 (R2)
    int insertIfAbsent(@Param("equipmentId") int equipmentId,
                       @Param("dataTs") LocalDateTime dataTs,
                       @Param("batchId") int batchId,
                       @Param("failureProb") BigDecimal failureProb);
}