using System.Net.Http.Json;
using System.Text.Json;
using PopClient.Models;

namespace PopClient.Api;

// mes-api 호출 전부. 화면은 HTTP·JSON을 몰라도 됨
public class ApiClient
{
    // JSON 이름을 camelCase로 (AlarmId ↔ alarmId)
    private static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web);

    private readonly HttpClient http;

    public ApiClient(string baseUrl)
    {
        http = new HttpClient
        {
            BaseAddress = new Uri(baseUrl),
            Timeout = TimeSpan.FromSeconds(10)
        };
    }

    // ---------- 경보 ----------

    // 처리 안 끝난 경보 (OPEN + ACK)
    public Task<List<Alarm>> GetOpenAlarmsAsync() =>
        SendAsync<List<Alarm>>(HttpMethod.Get, "api/alarms?status=OPEN&status=ACK");

    public Task<Alarm> AckAsync(int alarmId, string ackedBy) =>
        SendAsync<Alarm>(HttpMethod.Patch, $"api/alarms/{alarmId}/ack", new AlarmAckRequest(ackedBy));

    public Task<Alarm> CloseAlarmAsync(int alarmId, string closedBy, string memo) =>
        SendAsync<Alarm>(HttpMethod.Patch, $"api/alarms/{alarmId}/close", new AlarmCloseRequest(closedBy, memo));

    // ---------- 작업지시 ----------

    public Task<WorkOrder> CreateWorkOrderAsync(int alarmId, WorkOrderCreateRequest request) =>
        SendAsync<WorkOrder>(HttpMethod.Post, $"api/alarms/{alarmId}/work-orders", request);

    // 진행 중인 작업지시 (WAITING + IN_PROGRESS)
    public Task<List<WorkOrder>> GetActiveWorkOrdersAsync() =>
        SendAsync<List<WorkOrder>>(HttpMethod.Get, "api/work-orders?status=WAITING&status=IN_PROGRESS");

    public Task<WorkOrder> StartWorkOrderAsync(int workOrderId, string changedBy) =>
        SendAsync<WorkOrder>(HttpMethod.Patch, $"api/work-orders/{workOrderId}/start",
            new WorkOrderActionRequest(changedBy, null));

    public Task<WorkOrder> CompleteWorkOrderAsync(int workOrderId, WorkOrderCompleteRequest request) =>
        SendAsync<WorkOrder>(HttpMethod.Patch, $"api/work-orders/{workOrderId}/complete", request);

    public Task<WorkOrder> CancelWorkOrderAsync(int workOrderId, string changedBy, string? memo) =>
        SendAsync<WorkOrder>(HttpMethod.Patch, $"api/work-orders/{workOrderId}/cancel",
            new WorkOrderActionRequest(changedBy, memo));

    // ---------- 공통 ----------

    // 요청을 보내고, 성공이면 본문을 T로, 실패면 ApiException
    private async Task<T> SendAsync<T>(HttpMethod method, string path, object? body = null)
    {
        using var request = new HttpRequestMessage(method, path);
        if (body != null)
        {
            request.Content = JsonContent.Create(body, options: Json);
        }

        HttpResponseMessage response;
        try
        {
            response = await http.SendAsync(request);
        }
        catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
        {
            // 서버가 꺼져 있거나 10초 안에 응답이 없음
            throw new ApiException(0, "CONNECTION_FAILED", "서버에 연결할 수 없습니다. mes-api가 켜져 있는지 확인하세요");
        }

        using (response)
        {
            if (response.IsSuccessStatusCode)
            {
                return (await response.Content.ReadFromJsonAsync<T>(Json))!;
            }

            // 서버의 {code, message}를 꺼내 예외로
            ErrorResponse? error = null;
            try
            {
                error = await response.Content.ReadFromJsonAsync<ErrorResponse>(Json);
            }
            catch (JsonException)
            {
                // 본문이 우리 형식이 아님
            }
            throw new ApiException((int)response.StatusCode,
                error?.Code ?? "UNKNOWN",
                error?.Message ?? $"서버 응답 오류 ({(int)response.StatusCode})");
        }
    }
}