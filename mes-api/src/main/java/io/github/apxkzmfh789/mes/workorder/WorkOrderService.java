package io.github.apxkzmfh789.mes.workorder;

import io.github.apxkzmfh789.mes.alarm.Alarm;
import io.github.apxkzmfh789.mes.alarm.AlarmService;
import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import io.github.apxkzmfh789.mes.history.HistoryMapper;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class WorkOrderService {

    private final WorkOrderMapper workOrderMapper;
    private final AlarmService alarmService;
    private final HistoryMapper historyMapper;

    public WorkOrderService(WorkOrderMapper workOrderMapper, AlarmService alarmService,
                            HistoryMapper historyMapper) {
        this.workOrderMapper = workOrderMapper;
        this.alarmService = alarmService;
        this.historyMapper = historyMapper;
    }

    public WorkOrder findById(int workOrderId) {
        WorkOrder workOrder = workOrderMapper.findById(workOrderId);
        if (workOrder == null) {
            throw new BusinessException(ErrorCode.WORK_ORDER_NOT_FOUND, workOrderId);
        }
        return workOrder;
    }

    // 생성: ACK 경보에서만, 경보당 진행 중 1개 (R10)
    @Transactional
    public WorkOrder create(int alarmId, WorkOrderCreateRequest request) {
        Integer workOrderId;
        try {
            workOrderId = workOrderMapper.insertIfAlarmAcked(alarmId, request);
        } catch (DuplicateKeyException e) {
            // 동시 생성으로 조건 검사를 둘 다 통과한 경우, 고유 인덱스가 막음
            throw new BusinessException(ErrorCode.ACTIVE_WORK_ORDER_EXISTS, "alarmId " + alarmId);
        }

        if (workOrderId == null) {
            Alarm alarm = alarmService.findById(alarmId);   // 없으면 404
            if ("ACK".equals(alarm.status())) {
                throw new BusinessException(ErrorCode.ACTIVE_WORK_ORDER_EXISTS, "alarmId " + alarmId);
            }
            throw new BusinessException(ErrorCode.ALARM_STATUS_CONFLICT,
                    "alarmId " + alarmId + ", 현재 상태 " + alarm.status());
        }

        historyMapper.insert("WORK_ORDER", workOrderId, null, "WAITING", request.createdBy(), null);
        return findById(workOrderId);
    }
}