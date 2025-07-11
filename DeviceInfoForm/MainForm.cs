using System;
using System.Drawing;
using System.Windows.Forms;

namespace DeviceInfoForm
{
    public partial class MainForm : Form
    {
        private TextBox txtModel;
        private TextBox txtDeviceId;
        private TextBox txtCustomerCode;
        private TextBox txtFirmwareVersion;
        private Button btnClear;
        private Button btnSubmit;

        public MainForm()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.SuspendLayout();

            // Form properties
            this.Text = "Device Information Form";
            this.Size = new Size(400, 300);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;

            // Model Label and TextBox
            Label lblModel = new Label();
            lblModel.Text = "Model no. (Model):";
            lblModel.Location = new Point(20, 20);
            lblModel.Size = new Size(120, 23);
            this.Controls.Add(lblModel);

            txtModel = new TextBox();
            txtModel.Location = new Point(150, 20);
            txtModel.Size = new Size(200, 23);
            this.Controls.Add(txtModel);

            // IMEI Label and TextBox
            Label lblDeviceId = new Label();
            lblDeviceId.Text = "IMEI (DeviceId):";
            lblDeviceId.Location = new Point(20, 60);
            lblDeviceId.Size = new Size(120, 23);
            this.Controls.Add(lblDeviceId);

            txtDeviceId = new TextBox();
            txtDeviceId.Location = new Point(150, 60);
            txtDeviceId.Size = new Size(200, 23);
            this.Controls.Add(txtDeviceId);

            // CSC Label and TextBox
            Label lblCustomerCode = new Label();
            lblCustomerCode.Text = "CSC (CustomerCode):";
            lblCustomerCode.Location = new Point(20, 100);
            lblCustomerCode.Size = new Size(120, 23);
            this.Controls.Add(lblCustomerCode);

            txtCustomerCode = new TextBox();
            txtCustomerCode.Location = new Point(150, 100);
            txtCustomerCode.Size = new Size(200, 23);
            this.Controls.Add(txtCustomerCode);

            // OTA Source Label and TextBox
            Label lblFirmwareVersion = new Label();
            lblFirmwareVersion.Text = "OTA source (FirmwareVersion):";
            lblFirmwareVersion.Location = new Point(20, 140);
            lblFirmwareVersion.Size = new Size(120, 23);
            lblFirmwareVersion.AutoSize = true;
            this.Controls.Add(lblFirmwareVersion);

            txtFirmwareVersion = new TextBox();
            txtFirmwareVersion.Location = new Point(150, 140);
            txtFirmwareVersion.Size = new Size(200, 23);
            this.Controls.Add(txtFirmwareVersion);

            // Clear Button
            btnClear = new Button();
            btnClear.Text = "Clear";
            btnClear.Location = new Point(150, 200);
            btnClear.Size = new Size(75, 30);
            btnClear.Click += BtnClear_Click;
            this.Controls.Add(btnClear);

            // Submit Button
            btnSubmit = new Button();
            btnSubmit.Text = "Submit";
            btnSubmit.Location = new Point(275, 200);
            btnSubmit.Size = new Size(75, 30);
            btnSubmit.Click += BtnSubmit_Click;
            this.Controls.Add(btnSubmit);

            this.ResumeLayout(false);
        }

        private void BtnClear_Click(object? sender, EventArgs e)
        {
            txtModel.Clear();
            txtDeviceId.Clear();
            txtCustomerCode.Clear();
            txtFirmwareVersion.Clear();
        }

        private void BtnSubmit_Click(object? sender, EventArgs e)
        {
            string model = txtModel.Text;
            string deviceId = txtDeviceId.Text;
            string customerCode = txtCustomerCode.Text;
            string firmwareVersion = txtFirmwareVersion.Text;

            // Display the entered information
            string message = $"Device Information:\n\n" +
                           $"Model: {model}\n" +
                           $"IMEI (DeviceId): {deviceId}\n" +
                           $"CSC (CustomerCode): {customerCode}\n" +
                           $"OTA source (FirmwareVersion): {firmwareVersion}";

            MessageBox.Show(message, "Device Information", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }
}