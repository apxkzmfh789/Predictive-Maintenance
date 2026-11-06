package io.github.apxkzmfh789.mes.stats;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface StatsMapper {

    // from 이상 to 미만, 처리 시각 기준 (D12)
    List<EquipmentStats> findEquipmentStats(@Param("from") LocalDateTime from,
                                            @Param("to") LocalDateTime to);

    List<DailyStats> findDailyStats(@Param("from") LocalDateTime from,
                                    @Param("to") LocalDateTime to);
}