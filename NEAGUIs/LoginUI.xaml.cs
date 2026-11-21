using System.IO;
using System.Windows;

namespace NEAGUIs
{
    public partial class LoginUI : UI
    {
        private dynamic userAuth;
        private bool userExists;

        public LoginUI()
        {
            InitializeComponent();

            // Build user file path using SaveData
            string userFilePath = Path.Combine(saveData, "user_data.json");

            // Create Python auth controller
            userAuth = PyControllers.GetOrCreate(
                key: "Auth",
                moduleName: "UserAuth",
                className: "UserAuth",
                args: userFilePath
            );

            // Initialise UI based on whether user exists
            userExists = userAuth.is_user_registered();

            TitleText.Text = userExists ? "LOGIN" : "SIGN UP";
            SubmitButton.Content = userExists ? "Login" : "Create Account";
        }

        private void SubmitButton_Click(object sender, RoutedEventArgs e)
        {
            var username = UsernameBox.Text.Trim();
            var password = PasswordBox.Password.Trim();

            if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
            {
                MessageBox.Show("Please enter both username and password.");
                return;
            }

            if (userExists)
            {
                bool? ok = userAuth._verifyUser(password);

                if (ok == null)
                {
                    MessageBox.Show("User file missing or corrupted.");
                    return;
                }

                if (ok == true)
                {
                    NavigateTo<MainMenuUI>();
                }
                else
                {
                    MessageBox.Show("Incorrect password.");
                }
            }
            else
            {
                bool created = userAuth.register(password);

                if (created)
                {
                    NavigateTo<MainMenuUI>();
                }
                else
                {
                    MessageBox.Show("User already exists.");
                }
            }
        }
    }
}