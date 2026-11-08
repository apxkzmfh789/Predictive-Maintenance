namespace PopClient.Models;

// 서버 Alarm 레코드와 같은 모양 (GET /api/alarms 응답)
public record Alarm(
    int AlarmId,
    int EquipmentId,
    string EquipmentCode,
    string EquipmentName,
    int BatchId,
    string Status,
    DateTime FirstDetectedTs,
    DateTime LastDetectedTs,
    decimal MaxProb,
    int DetectCount,
    DateTime CreatedAt,
    DateTime? AckedAt,
    string? AckedBy,
    DateTime? ClosedAt,
    string? ClosedBy,
    string? CloseReason,
    string? CloseMemo,
    DateTime? CloseDataTs
);