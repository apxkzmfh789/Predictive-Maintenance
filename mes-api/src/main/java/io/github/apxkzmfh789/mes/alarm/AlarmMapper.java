package io.github.apxkzmfh789.mes.alarm;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface AlarmMapper {

    // 설비의 열린 경보(OPEN·ACK) ID, 없으면 null (R6)
    Integer findOpenAlarmId(int equipmentId);

    // 설비의 마지막 종료 경보의 종료 데이터 시각, 없으면 null (R7)
    LocalDateTime findLastCloseDataTs(int equipmentId);

    // 새 경보 생성, 새 alarm_id 반환
    int insert(@Param("equipmentId") int equipmentId,
               @Param("batchId") int batchId,
               @Param("result") JudgeResult result);

    // 열린 경보에 감지 내용 반영 (R6)
    int updateDetection(@Param("alarmId") int alarmId,
                        @Param("result") JudgeResult result);

    // 목록, 조건이 null이면 그 조건은 무시
    List<Alarm> findAll(@Param("statuses") List<String> statuses,
                        @Param("equipmentId") Integer equipmentId);

    // 상세, 없으면 null
    Alarm findById(int alarmId);

    // OPEN일 때만 ACK로, 바뀐 행 수 반환 (0이면 거부, R17)
    int ack(@Param("alarmId") int alarmId, @Param("ackedBy") String ackedBy);
}