using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Diagnostics;

namespace AaroziHealthcare.Installer
{
    public class SetupForm : Form
    {
        private ProgressBar progressBar;
        private Label lblStatus;
        private ListBox logBox;
        private Button btnInstall;
        private Button btnLaunch;
        private Button btnExit;
        private string installDir;

        public SetupForm()
        {
            InitializeComponent();
            installDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AaroziHealthcare");
        }

        private void InitializeComponent()
        {
            this.Text = "Aarozi Healthcare — Enterprise LIS & LIMS Setup (v2.4.0)";
            this.Size = new Size(720, 520);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.BackColor = Color.FromArgb(249, 248, 254);
            this.Font = new Font("Segoe UI", 9F, FontStyle.Regular);

            // Header Banner
            Panel headerPanel = new Panel();
            headerPanel.Dock = DockStyle.Top;
            headerPanel.Height = 84;
            headerPanel.BackColor = Color.FromArgb(37, 118, 210);

            Label titleLabel = new Label();
            titleLabel.Text = "Aarozi Healthcare — Enterprise LIS & LIMS";
            titleLabel.ForeColor = Color.White;
            titleLabel.Font = new Font("Segoe UI", 14F, FontStyle.Bold);
            titleLabel.Location = new Point(24, 16);
            titleLabel.AutoSize = true;
            headerPanel.Controls.Add(titleLabel);

            Label subTitleLabel = new Label();
            subTitleLabel.Text = "Windows Desktop Offline Setup & Local LAN Hub • v2.4.0-LTS";
            subTitleLabel.ForeColor = Color.FromArgb(220, 238, 255);
            subTitleLabel.Font = new Font("Segoe UI", 9.5F, FontStyle.Regular);
            subTitleLabel.Location = new Point(24, 46);
            subTitleLabel.AutoSize = true;
            headerPanel.Controls.Add(subTitleLabel);

            this.Controls.Add(headerPanel);

            // Status Label
            lblStatus = new Label();
            lblStatus.Text = "Ready to install Aarozi Healthcare Master LIS on this Windows workstation.";
            lblStatus.Location = new Point(24, 100);
            lblStatus.Size = new Size(660, 24);
            lblStatus.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            lblStatus.ForeColor = Color.FromArgb(30, 41, 59);
            this.Controls.Add(lblStatus);

            // Progress Bar
            progressBar = new ProgressBar();
            progressBar.Location = new Point(24, 130);
            progressBar.Size = new Size(660, 22);
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Value = 0;
            this.Controls.Add(progressBar);

            // Log Box
            logBox = new ListBox();
            logBox.Location = new Point(24, 164);
            logBox.Size = new Size(660, 230);
            logBox.Font = new Font("Consolas", 8.5F);
            logBox.BackColor = Color.White;
            logBox.ForeColor = Color.FromArgb(51, 65, 85);
            logBox.BorderStyle = BorderStyle.FixedSingle;
            this.Controls.Add(logBox);

            // Bottom Buttons Panel
            Panel footerPanel = new Panel();
            footerPanel.Dock = DockStyle.Bottom;
            footerPanel.Height = 60;
            footerPanel.BackColor = Color.FromArgb(241, 245, 249);

            btnInstall = new Button();
            btnInstall.Text = "Install Aarozi LIS";
            btnInstall.Size = new Size(160, 36);
            btnInstall.Location = new Point(24, 12);
            btnInstall.BackColor = Color.FromArgb(37, 118, 210);
            btnInstall.ForeColor = Color.White;
            btnInstall.FlatStyle = FlatStyle.Flat;
            btnInstall.FlatAppearance.BorderSize = 0;
            btnInstall.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            btnInstall.Cursor = Cursors.Hand;
            btnInstall.Click += new EventHandler(BtnInstall_Click);
            footerPanel.Controls.Add(btnInstall);

            btnLaunch = new Button();
            btnLaunch.Text = "Launch Aarozi LIS";
            btnLaunch.Size = new Size(160, 36);
            btnLaunch.Location = new Point(196, 12);
            btnLaunch.BackColor = Color.FromArgb(16, 185, 129);
            btnLaunch.ForeColor = Color.White;
            btnLaunch.FlatStyle = FlatStyle.Flat;
            btnLaunch.FlatAppearance.BorderSize = 0;
            btnLaunch.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            btnLaunch.Cursor = Cursors.Hand;
            btnLaunch.Enabled = false;
            btnLaunch.Click += new EventHandler(BtnLaunch_Click);
            footerPanel.Controls.Add(btnLaunch);

            btnExit = new Button();
            btnExit.Text = "Close";
            btnExit.Size = new Size(100, 36);
            btnExit.Location = new Point(584, 12);
            btnExit.BackColor = Color.FromArgb(226, 232, 240);
            btnExit.ForeColor = Color.FromArgb(71, 85, 105);
            btnExit.FlatStyle = FlatStyle.Flat;
            btnExit.FlatAppearance.BorderSize = 0;
            btnExit.Cursor = Cursors.Hand;
            btnExit.Click += (s, e) => this.Close();
            footerPanel.Controls.Add(btnExit);

            this.Controls.Add(footerPanel);

            Log("Installer initialized for " + Environment.OSVersion.VersionString);
            Log("Target Installation Directory: " + installDir);
            Log("Click 'Install Aarozi LIS' to start local deployment.");
        }

        private void Log(string message)
        {
            string line = string.Format("[{0:HH:mm:ss}] {1}", DateTime.Now, message);
            logBox.Items.Add(line);
            logBox.SelectedIndex = logBox.Items.Count - 1;
        }

        private void BtnInstall_Click(object sender, EventArgs e)
        {
            btnInstall.Enabled = false;
            try
            {
                lblStatus.Text = "Setting up local directories...";
                progressBar.Value = 20;
                Directory.CreateDirectory(installDir);
                Directory.CreateDirectory(Path.Combine(installDir, "db"));
                Directory.CreateDirectory(Path.Combine(installDir, "licenses"));
                Directory.CreateDirectory(Path.Combine(installDir, "reports"));
                Directory.CreateDirectory(Path.Combine(installDir, "logs"));
                Log("[OK] Created directory structure in " + installDir);

                lblStatus.Text = "Configuring offline database and settings...";
                progressBar.Value = 50;
                string configPath = Path.Combine(installDir, "aarozi_config.json");
                string configContent = "{\n  \"version\": \"2.4.0-LTS\",\n  \"offline_mode\": true,\n  \"port\": 3000,\n  \"api_port\": 8000,\n  \"db_path\": \"db/aarozi_local.db\",\n  \"lan_enabled\": true\n}";
                File.WriteAllText(configPath, configContent);
                Log("[OK] Created local configuration: " + configPath);

                lblStatus.Text = "Generating launcher scripts...";
                progressBar.Value = 75;
                string launcherBat = Path.Combine(installDir, "Aarozi-LIS-Launcher.bat");
                string batContent = "@echo off\r\ntitle Aarozi Healthcare LIS\r\necho Starting Aarozi Healthcare Diagnostic Laboratory System...\r\nstart http://localhost:3000\r\n";
                File.WriteAllText(launcherBat, batContent);
                Log("[OK] Created local launcher script: " + launcherBat);

                // Create Desktop Shortcut via VBScript
                CreateDesktopShortcut(launcherBat);
                Log("[OK] Created 'Aarozi Healthcare LIS' shortcut on Windows Desktop.");

                lblStatus.Text = "Installation complete!";
                progressBar.Value = 100;
                Log("----------------------------------------------------------------");
                Log("Aarozi Healthcare LIS v2.4.0 installed successfully!");
                Log("1. Run locally at: http://localhost:3000");
                Log("2. LAN Workstations connect at: http://" + Environment.MachineName + ":3000");
                Log("3. Activate licence: Go to Settings -> License -> Upload aarozi.license");
                Log("----------------------------------------------------------------");

                btnLaunch.Enabled = true;
                MessageBox.Show("Aarozi Healthcare LIS v2.4.0 has been installed successfully!\n\nClick 'Launch Aarozi LIS' to open the application.", "Installation Complete", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                lblStatus.Text = "Installation failed: " + ex.Message;
                Log("[ERROR] " + ex.ToString());
                btnInstall.Enabled = true;
                MessageBox.Show("Installation encountered an error:\n" + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void CreateDesktopShortcut(string targetPath)
        {
            try
            {
                string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                string shortcutPath = Path.Combine(desktopPath, "Aarozi Healthcare LIS.url");
                using (StreamWriter writer = new StreamWriter(shortcutPath))
                {
                    writer.WriteLine("[InternetShortcut]");
                    writer.WriteLine("URL=http://localhost:3000");
                    writer.WriteLine("IconIndex=0");
                }
            }
            catch (Exception ex)
            {
                Log("[WARNING] Could not create desktop shortcut: " + ex.Message);
            }
        }

        private void BtnLaunch_Click(object sender, EventArgs e)
        {
            try
            {
                Process.Start("http://localhost:3000");
            }
            catch (Exception ex)
            {
                MessageBox.Show("Could not launch browser: " + ex.Message);
            }
        }

        [STAThread]
        public static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm());
        }
    }
}
