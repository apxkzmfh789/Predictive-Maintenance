package io.github.apxkzmfh789.mes.equipment;

import io.github.apxkzmfh789.mes.common.BusinessException;
import io.github.apxkzmfh789.mes.common.ErrorCode;
import org.springframework.stereotype.Service;

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
}
