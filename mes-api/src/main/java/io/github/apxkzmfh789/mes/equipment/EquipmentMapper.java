package io.github.apxkzmfh789.mes.equipment;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface EquipmentMapper {
    // SELECT 결과 여러 행 -> Equipment 목록
    List<Equipment> findAll();

    // 결과가 없으면 null
    Equipment findById(int equipmentId);

    // 결과가 없으면 null
    Equipment findByCode(String equipmentCode);

    // 들어간 행 수 반환
    int insert(EquipmentCreateRequest request);

    int update(@Param("equipmentId") int equipmentId,
               @Param("request") EquipmentUpdateRequest request);

    // 현재 상태가 맞을 때만 변경, 바뀐 행 수 반환 (R13, R17)
    int updateStatus(@Param("equipmentId") int equipmentId,
                     @Param("fromStatus") String fromStatus,
                     @Param("toStatus") String toStatus);
}
