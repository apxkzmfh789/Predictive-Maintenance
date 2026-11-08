namespace PopClient.Models;

// 서버 WorkOrder 레코드와 같은 모양
public record WorkOrder(
    int WorkOrderId,
    int AlarmId,
    int EquipmentId,
    string EquipmentCode,
    string EquipmentName,
    string Status,
    string WorkType,
    string Assignee,
    string? Instruction,
    string? ResultCode,
    string? ActionNote,
    string CreatedBy,
    DateTime CreatedAt,
    DateTime? StartedAt,
    DateTime? CompletedAt,
    DateTime? CanceledAt
);