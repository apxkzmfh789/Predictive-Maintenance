package io.github.apxkzmfh789.mes.equipment;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

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

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Equipment create(@Valid @RequestBody EquipmentCreateRequest request){
        return equipmentService.create(request);
    }

    // PUT /api/equipments/{equipmentId}
    @PutMapping("/{equipmentId}")
    public Equipment update(@PathVariable int equipmentId,
                            @Valid @RequestBody EquipmentUpdateRequest request){
        return equipmentService.update(equipmentId, request);
    }
}
