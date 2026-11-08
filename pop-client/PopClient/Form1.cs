using PopClient.Api;

namespace PopClient
{
    public partial class Form1 : Form
    {
        private readonly ApiClient api = new("http://localhost:8080/");

        public Form1()
        {
            InitializeComponent();
            Load += Form1_Load;   // 창이 처음 뜰 때 실행
        }

        // (임시) 서버 연결 확인
        private async void Form1_Load(object? sender, EventArgs e)
        {
            try
            {
                var alarms = await api.GetOpenAlarmsAsync();
                var first = alarms.FirstOrDefault();
                MessageBox.Show($"열린 경보 {alarms.Count}건\n첫 경보: {first?.EquipmentCode} / {first?.Status} / 최고 확률 {first?.MaxProb}");
            }
            catch (ApiException ex)
            {
                MessageBox.Show(ex.Message, $"오류 ({ex.Code})");
            }
        }
    }
}