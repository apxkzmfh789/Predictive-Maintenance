namespace PopClient.Models;

// 요청 본문. 서버 Request 레코드와 이름을 맞춤 (보낼 때 camelCase로 바뀜)
public record AlarmAckRequest(string AckedBy);

public record AlarmCloseRequest(string ClosedBy, string Memo);

public record WorkOrderCreateRequest(string WorkType, string Assignee, string? Instruction, string CreatedBy);

public record WorkOrderActionRequest(string ChangedBy, string? Memo);

public record WorkOrderCompleteRequest(string ChangedBy, string ResultCode, string ActionNote);