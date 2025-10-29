from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']
flow = InstalledAppFlow.from_client_secrets_file(
    r'D:\Visualstudiocode\QRManaShinYi\webserver\client_secret_361170984881-6611kpd81k8otr4mvggd0ah8mqrkie46.apps.googleusercontent.com.json', SCOPES)
creds = flow.run_local_server(port=0)
with open(r'D:\Visualstudiocode\QRManaShinYi\webserver\client_secret_361170984881-6611kpd81k8otr4mvggd0ah8mqrkie46.apps.googleusercontent.com.json', 'w') as token:
    token.write(creds.to_json())