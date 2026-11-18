namespace PopClient
{
    // 작업 완료 입력 창: 결과 코드와 조치 내용 (R11, 둘 다 필수)
    public class CompleteDialog : Form
    {
        // 콤보박스 항목: 화면에는 한글, 서버에는 코드
        private record ResultItem(string Code, string Label)
        {
            public override string ToString() => $"{Label} ({Code})";
        }

        private readonly ComboBox cboResult = new();
        private readonly TextBox txtActionNote = new();

        public string ResultCode => ((ResultItem)cboResult.SelectedItem!).Code;
        public string ActionNote => txtActionNote.Text.Trim();

        public CompleteDialog(string title)
        {
            SuspendLayout();

            cboResult.DropDownStyle = ComboBoxStyle.DropDownList;
            cboResult.Items.AddRange(new object[]
            {
                new ResultItem("NO_ISSUE", "이상 없음"),
                new ResultItem("ADJUSTED", "조정"),
                new ResultItem("PART_REPLACED", "부품 교체"),
                new ResultItem("REPAIRED", "수리")
            });
            cboResult.SelectedIndex = 1;   // 기본값 조정
            cboResult.Dock = DockStyle.Fill;

            txtActionNote.Multiline = true;
            txtActionNote.MaxLength = 1000;   // 서버 @Size(max = 1000)
            txtActionNote.ScrollBars = ScrollBars.Vertical;
            txtActionNote.PlaceholderText = "한 일과 결과 (필수)";
            txtActionNote.Dock = DockStyle.Fill;

            var table = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 2 };
            table.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
            table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
            table.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            table.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            table.Controls.Add(NewLabel("결과"), 0, 0);
            table.Controls.Add(cboResult, 1, 0);
            table.Controls.Add(NewLabel("조치 내용"), 0, 1);
            table.Controls.Add(txtActionNote, 1, 1);

            var btnOk = new Button { Text = "완료", AutoSize = true };
            var btnCancel = new Button { Text = "취소", AutoSize = true, DialogResult = DialogResult.Cancel };
            btnOk.Click += BtnOk_Click;

            var buttons = new FlowLayoutPanel
            {
                Dock = DockStyle.Bottom,
                AutoSize = true,
                FlowDirection = FlowDirection.RightToLeft,
                Padding = new Padding(0, 6, 0, 0)
            };
            buttons.Controls.Add(btnCancel);
            buttons.Controls.Add(btnOk);

            var body = new Panel { Dock = DockStyle.Fill, Padding = new Padding(12) };
            body.Controls.Add(table);
            body.Controls.Add(buttons);
            Controls.Add(body);

            AcceptButton = btnOk;
            CancelButton = btnCancel;
            Text = title;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.CenterParent;
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(440, 240);
            ResumeLayout(false);
            PerformLayout();
        }

        private static Label NewLabel(string text) =>
            new() { Text = text, AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(3, 6, 12, 3) };

        private void BtnOk_Click(object? sender, EventArgs e)
        {
            if (ActionNote.Length == 0)
            {
                MessageBox.Show("조치 내용을 입력하세요", Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
                txtActionNote.Focus();
                return;
            }
            DialogResult = DialogResult.OK;
        }
    }
}