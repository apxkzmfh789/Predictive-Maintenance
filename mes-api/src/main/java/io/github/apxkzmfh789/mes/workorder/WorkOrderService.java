package io.github.apxkzmfh789.mes.workorder;

import io.github.apxkzmfh789.mes.alarm.Alarm;
import io.github.apxkzmfh789.mes.alarm.AlarmService;
import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import io.github.apxkzmfh789.mes.equipment.Equipment;
import io.github.apxkzmfh789.mes.equipment.EquipmentService;
import io.github.apxkzmfh789.mes.history.HistoryMapper;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Set;

@Service
public class WorkOrderService {

    private static final Set<String> STATUSES = Set.of("WAITING", "IN_PROGRESS", "DONE", "CANCELED");

    private final WorkOrderMapper workOrderMapper;
    private final AlarmService alarmService;
    private final EquipmentService equipmentService;
    private final HistoryMapper historyMapper;

    public WorkOrderService(WorkOrderMapper workOrderMapper, AlarmService alarmService, EquipmentService equipmentService,
                            HistoryMapper historyMapper) {
        this.workOrderMapper = workOrderMapper;
        this.alarmService = alarmService;
        this.equipmentService = equipmentService;
        this.historyMapper = historyMapper;
    }

    public List<WorkOrder> findAll(List<String> statuses, Integer equipmentId) {
        if (statuses != null) {
            for (String status : statuses) {
                if (!STATUSES.contains(status)) {
                    throw new BusinessException(ErrorCode.INVALID_INPUT,
                            "status는 WAITING, IN_PROGRESS, DONE, CANCELED 중 하나: " + status);
                }
            }
        }
        return workOrderMapper.findAll(statuses, equipmentId);
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

    // 시작: WAITING → IN_PROGRESS, 설비 RUNNING → MAINTENANCE (R13, R17)
    @Transactional
    public WorkOrder start(int workOrderId, WorkOrderActionRequest request) {
        int updated = workOrderMapper.start(workOrderId);
        if (updated == 0) {
            throw statusConflictOrNotFound(workOrderId);
        }
        historyMapper.insert("WORK_ORDER", workOrderId, "WAITING", "IN_PROGRESS",
                request.changedBy(), request.memo());

        WorkOrder workOrder = findById(workOrderId);
        equipmentService.changeStatus(workOrder.equipmentId(), "RUNNING", "MAINTENANCE",
                request.changedBy(), "작업지시 " + workOrderId + " 시작");
        return workOrder;
    }

    // 0건일 때 이유 구분: 없으면 404, 상태가 안 맞으면 409
    private BusinessException statusConflictOrNotFound(int workOrderId) {
        WorkOrder workOrder = findById(workOrderId);   // 없으면 404
        return new BusinessException(ErrorCode.WORK_ORDER_STATUS_CONFLICT,
                "workOrderId " + workOrderId + ", 현재 상태 " + workOrder.status());
    }
}