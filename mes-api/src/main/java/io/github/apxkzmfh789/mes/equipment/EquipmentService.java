package io.github.apxkzmfh789.mes.equipment;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class EquipmentService {

    private final EquipmentMapper equipmentMapper;

    public EquipmentService(EquipmentMapper equipmentMapper) {
        this.equipmentMapper = equipmentMapper;
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
}
