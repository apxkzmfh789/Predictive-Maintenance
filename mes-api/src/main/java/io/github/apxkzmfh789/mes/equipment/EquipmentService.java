package io.github.apxkzmfh789.mes.equipment;

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
}
