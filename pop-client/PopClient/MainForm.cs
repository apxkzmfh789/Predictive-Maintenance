using PopClient.Api;
using PopClient.Models;

namespace PopClient
{
    public partial class MainForm : Form
    {
        private readonly ApiClient api = new("http://localhost:8080/");
        private bool loading;   // 갱신이 겹치지 않게

        public MainForm()
        {
            InitializeComponent();
            SetupColumns();

            // 목록 갱신: 창이 뜰 때, 새로고침 버튼, 10초 타이머
            Load += MainForm_Load;
            btnRefresh.Click += BtnRefresh_Click;
            refreshTimer.Tick += RefreshTimer_Tick;

            // 표
            dgvAlarms.CellFormatting += DgvAlarms_CellFormatting;
            dgvAlarms.SelectionChanged += DgvAlarms_SelectionChanged;

            // 경보 처리 버튼
            btnAck.Click += BtnAck_Click;
            btnCloseAlarm.Click += BtnCloseAlarm_Click;
            btnCreateWorkOrder.Click += BtnCreateWorkOrder_Click;
            btnWorkOrders.Click += BtnWorkOrders_Click;

            UpdateButtons();
            refreshTimer.Start();
        }

        // ---------- 목록 갱신 이벤트 ----------

        private async void MainForm_Load(object? sender, EventArgs e) => await LoadAlarmsAsync();

        private async void BtnRefresh_Click(object? sender, EventArgs e) => await LoadAlarmsAsync();

        private async void RefreshTimer_Tick(object? sender, EventArgs e) => await LoadAlarmsAsync();

        // OPEN = 아직 아무도 안 봄 → 빨강, ACK = 처리 중 → 노랑
        private void DgvAlarms_CellFormatting(object? sender, DataGridViewCellFormattingEventArgs e)
        {
            if (e.RowIndex < 0 || e.CellStyle == null) return;
            if (dgvAlarms.Rows[e.RowIndex].DataBoundItem is not Alarm alarm) return;
            e.CellStyle.BackColor = alarm.Status == "OPEN" ? Color.MistyRose : Color.LightYellow;
        }

        private void DgvAlarms_SelectionChanged(object? sender, EventArgs e) => UpdateButtons();

        // ---------- 경보 처리 버튼 ----------

        // 확인: OPEN → ACK
        private async void BtnAck_Click(object? sender, EventArgs e)
        {
            var alarm = SelectedAlarm();
            var worker = RequireWorker();
            if (alarm == null || worker == null) return;

            await RunActionAsync(() => api.AckAsync(alarm.AlarmId, worker));
        }

        // 오경보 종료: 메모 필수 (R9)
        private async void BtnCloseAlarm_Click(object? sender, EventArgs e)
        {
            var alarm = SelectedAlarm();
            var worker = RequireWorker();
            if (alarm == null || worker == null) return;

            using var dialog = new MemoDialog("오경보 종료",
                $"경보 {alarm.AlarmId} ({alarm.EquipmentCode})를 오경보로 종료합니다.\n종료 사유를 입력하세요.",
                required: true);
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            string memo = dialog.Memo!;

            await RunActionAsync(() => api.CloseAlarmAsync(alarm.AlarmId, worker, memo));
        }

        // 작업지시 생성: ACK 경보에서만 (R10)
        private async void BtnCreateWorkOrder_Click(object? sender, EventArgs e)
        {
            var alarm = SelectedAlarm();
            var worker = RequireWorker();
            if (alarm == null || worker == null) return;

            using var dialog = new WorkOrderDialog($"작업지시 생성 - 경보 {alarm.AlarmId} ({alarm.EquipmentCode})");
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            var request = new WorkOrderCreateRequest(dialog.WorkType, dialog.Assignee, dialog.Instruction, worker);

            await RunActionAsync(async () =>
            {
                var workOrder = await api.CreateWorkOrderAsync(alarm.AlarmId, request);
                MessageBox.Show($"작업지시 {workOrder.WorkOrderId} 생성 (담당 {workOrder.Assignee})", "작업지시");
            });
        }

        // 작업지시 창 열기: 같은 작업자 이름으로 처리, 닫으면 경보 목록 갱신
        private async void BtnWorkOrders_Click(object? sender, EventArgs e)
        {
            var worker = RequireWorker();
            if (worker == null) return;

            using (var form = new WorkOrderForm(api, worker))
            {
                form.ShowDialog(this);
            }
            await LoadAlarmsAsync();
        }

        // 버튼 동작 공통: 처리 중엔 버튼 잠금, 실패하면 서버 메시지 팝업, 끝나면 목록 갱신
        private async Task RunActionAsync(Func<Task> action)
        {
            bottomPanel.Enabled = false;
            try
            {
                await action();
            }
            catch (ApiException ex)
            {
                MessageBox.Show(ex.Message, "처리 실패", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            finally
            {
                bottomPanel.Enabled = true;
                await LoadAlarmsAsync();
            }
        }

        // 작업자 이름 (R16: 로그인 대신 이름으로 기록). 비어 있으면 안내 후 null
        private string? RequireWorker()
        {
            var name = txtWorker.Text.Trim();
            if (name.Length == 0)
            {
                MessageBox.Show("작업자 이름을 먼저 입력하세요", "작업자", MessageBoxButtons.OK, MessageBoxIcon.Information);
                txtWorker.Focus();
                return null;
            }
            return name;
        }

        // 상태에 맞는 버튼만 켬 (R8). 화면 정보가 오래됐을 수 있어 최종 판단은 서버가 함
        private void UpdateButtons()
        {
            var status = SelectedAlarm()?.Status;
            btnAck.Enabled = status == "OPEN";
            btnCloseAlarm.Enabled = status == "ACK";
            btnCreateWorkOrder.Enabled = status == "ACK";
        }

        // ---------- 경보 목록 ----------

        private async Task LoadAlarmsAsync()
        {
            if (loading) return;
            loading = true;
            try
            {
                int? selectedId = SelectedAlarm()?.AlarmId;
                var alarms = await api.GetOpenAlarmsAsync();
                dgvAlarms.DataSource = alarms;
                RestoreSelection(selectedId);
                lblStatus.Text = $"열린 경보 {alarms.Count}건 · {DateTime.Now:HH:mm:ss} 갱신";
            }
            catch (ApiException ex)
            {
                // 자동 갱신 실패는 팝업 대신 상태 글자로 (10초마다 팝업이 쌓이지 않게)
                lblStatus.Text = $"갱신 실패: {ex.Message}";
            }
            finally
            {
                loading = false;
                UpdateButtons();
            }
        }

        // 표에서 선택된 줄의 경보, 없으면 null
        private Alarm? SelectedAlarm() => dgvAlarms.CurrentRow?.DataBoundItem as Alarm;

        // 새로고침 전에 선택했던 경보를 다시 선택
        private void RestoreSelection(int? alarmId)
        {
            if (alarmId == null) return;
            foreach (DataGridViewRow row in dgvAlarms.Rows)
            {
                if (row.DataBoundItem is Alarm alarm && alarm.AlarmId == alarmId)
                {
                    dgvAlarms.CurrentCell = row.Cells[0];
                    return;
                }
            }
        }

        // ---------- 표 열 ----------

        private void SetupColumns()
        {
            dgvAlarms.AutoGenerateColumns = false;
            AddColumn(nameof(Alarm.AlarmId), "경보", 50);
            AddColumn(nameof(Alarm.EquipmentCode), "설비", 70);
            AddColumn(nameof(Alarm.EquipmentName), "설비명", 110);
            AddColumn(nameof(Alarm.Status), "상태", 60);
            AddColumn(nameof(Alarm.MaxProb), "최고 확률", 70, "0.000");
            AddColumn(nameof(Alarm.DetectCount), "감지", 50);
            AddColumn(nameof(Alarm.FirstDetectedTs), "최초 감지", 110, "MM-dd HH:mm");
            AddColumn(nameof(Alarm.LastDetectedTs), "최근 감지", 110, "MM-dd HH:mm");
            AddColumn(nameof(Alarm.AckedBy), "확인자", 70);
        }

        private void AddColumn(string property, string header, float weight, string? format = null)
        {
            var column = new DataGridViewTextBoxColumn
            {
                DataPropertyName = property,
                HeaderText = header,
                FillWeight = weight
            };
            if (format != null)
            {
                column.DefaultCellStyle.Format = format;
            }
            dgvAlarms.Columns.Add(column);
        }
    }
}