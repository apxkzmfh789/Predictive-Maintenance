package io.github.apxkzmfh789.mes.workorder;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface WorkOrderMapper {

    // 경보가 ACK이고 진행 중 작업지시가 없을 때만 생성, 새 번호 반환 (조건 불만족이면 null, R10)
    Integer insertIfAlarmAcked(@Param("alarmId") int alarmId,
                               @Param("request") WorkOrderCreateRequest request);

    // 상세, 없으면 null
    WorkOrder findById(int workOrderId);

    // 목록, 조건이 null이면 무시
    List<WorkOrder> findAll(@Param("statuses") List<String> statuses,
                            @Param("equipmentId") Integer equipmentId);

    // WAITING일 때만 IN_PROGRESS로, 바뀐 행 수 반환 (R17)
    int start(int workOrderId);
}