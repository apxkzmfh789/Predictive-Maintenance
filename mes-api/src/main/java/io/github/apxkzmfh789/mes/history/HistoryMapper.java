package io.github.apxkzmfh789.mes.history;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface HistoryMapper {

    // 상태 변경 한 건 기록 (R15)
    int insert(@Param("targetType") String targetType,
               @Param("targetId") int targetId,
               @Param("fromStatus") String fromStatus,
               @Param("toStatus") String toStatus,
               @Param("changedBy") String changedBy,
               @Param("memo") String memo);

    // 대상별 이력, 오래된 순. targetId가 null이면 그 종류 전체
    List<History> findByTarget(@Param("targetType") String targetType,
                               @Param("targetId") Integer targetId);
}