package io.github.apxkzmfh789.mes.prediction;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.math.BigDecimal;

@Mapper
public interface ImportBatchMapper {

    // 적재 이력 생성, 새 batch_id 반환
    int insert(@Param("fileName") String fileName,
               @Param("modelThreshold") BigDecimal modelThreshold,
               @Param("appliedThreshold") BigDecimal appliedThreshold,
               @Param("importedBy") String importedBy);

    // 적재가 끝난 뒤 건수, 시각 기록
    int updateResult(ImportResult result);
}
