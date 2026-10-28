package io.github.apxkzmfh789.mes.equipment;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface EquipmentMapper {
    // SELECT 결과 여러 행 -> Equipment 목록
    List<Equipment> findAll();
}
