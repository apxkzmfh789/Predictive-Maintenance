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

            // 이벤트 연결: 창이 뜰 때, 새로고침 버튼, 10초 타이머 → 전부 경보 다시 불러오기
            Load += MainForm_Load;
            btnRefresh.Click += BtnRefresh_Click;
            refreshTimer.Tick += RefreshTimer_Tick;
            dgvAlarms.CellFormatting += DgvAlarms_CellFormatting;
            refreshTimer.Start();
        }

        // ---------- 이벤트 ----------

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