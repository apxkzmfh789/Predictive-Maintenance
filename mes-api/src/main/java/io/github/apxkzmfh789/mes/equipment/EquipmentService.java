package io.github.apxkzmfh789.mes.equipment;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import io.github.apxkzmfh789.mes.history.HistoryMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class EquipmentService {

    private final EquipmentMapper equipmentMapper;
    private final HistoryMapper historyMapper;

    public EquipmentService(EquipmentMapper equipmentMapper, HistoryMapper historyMapper) {
        this.equipmentMapper = equipmentMapper;
        this.historyMapper = historyMapper;
    }

    public List<Equipment> findAll() {
        return equipmentMapper.findAll();
    }

    public Equipment findById(int equipmentId) {
        Equipment equipment = equipmentMapper.findById(equipmentId);
        if (equipment == null){
            throw new BusinessException(ErrorCode.EQUIPMENT_NOT_FOUND, equipmentId);
        }
        return equipment;
    }

    @Transactional
    public Equipment create(EquipmentCreateRequest request){
        // 같은 설비 코드가 있으면 거부
        if (equipmentMapper.findByCode(request.equipmentCode()) != null){
            throw new BusinessException(ErrorCode.EQUIPMENT_CODE_DUPLICATED, request.equipmentCode());
        }
        equipmentMapper.insert(request);

        // DEFAULT로 채워진 값까지 포함해서 돌려주려고 다시 조회
        return equipmentMapper.findByCode((request.equipmentCode()));
    }

    @Transactional
    public Equipment update(int equipmentId, EquipmentUpdateRequest request){
        // UPDATE 결과가 0행이면 그런 설비가 없음
        int updated = equipmentMapper.update(equipmentId, request);
        if (updated == 0) {
            throw new BusinessException(ErrorCode.EQUIPMENT_NOT_FOUND, equipmentId);
        }
        return equipmentMapper.findById(equipmentId);
    }

    // 설비 상태 변경 + 이력. 작업지시에서만 호출, Controller에 연결하지 않음 (R13, R14)
    @Transactional
    public void changeStatus(int equipmentId, String fromStatus, String toStatus,
                             String changedBy, String memo) {
        int updated = equipmentMapper.updateStatus(equipmentId, fromStatus, toStatus);
        if (updated == 0) {
            Equipment equipment = findById(equipmentId);   // 없으면 404
            throw new BusinessException(ErrorCode.EQUIPMENT_STATUS_CONFLICT,
                    "equipmentId " + equipmentId + ", 현재 상태 " + equipment.status());
        }
        historyMapper.insert("EQUIPMENT", equipmentId, fromStatus, toStatus, changedBy, memo);
    }
}
