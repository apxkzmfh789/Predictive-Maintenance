package io.github.apxkzmfh789.mes.equipment;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/equipments")
public class EquipmentController {

    private final EquipmentService equipmentService;

    public EquipmentController(EquipmentService equipmentService) {
        this.equipmentService = equipmentService;
    }

    // GET /api/equipments
    @GetMapping
    public List<Equipment> findAll(){
        return equipmentService.findAll();
    }

    // GET /api/equipments/{equipmentId}
    @GetMapping("/{equipmentId}")
    public Equipment findById(@PathVariable int equipmentId){
        return equipmentService.findById(equipmentId);
    }
}
