"""
Script para subir dataset automáticamente a Google Drive usando la API.

Requiere autenticación con Google Drive.
"""

from pathlib import Path
import sys

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    import pickle
    import os.path
except ImportError:
    print("❌ Dependencias no instaladas")
    print("\nInstala con:")
    print("  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Alcances de Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Archivo a subir
DATASET_ZIP = Path(__file__).parent.parent / 'exports' / 'sirccd_dataset_v1.0.0.zip'
CREDENTIALS_FILE = Path(__file__).parent.parent / 'google_credentials.json'
TOKEN_FILE = Path(__file__).parent.parent / 'token.pickle'


def authenticate():
    """Autentica con Google Drive."""
    creds = None
    
    # Token guardado de sesiones anteriores
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # Si no hay credenciales válidas, autenticar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print("❌ Archivo de credenciales no encontrado")
                print(f"\n1. Ve a: https://console.cloud.google.com/apis/credentials")
                print(f"2. Crea OAuth 2.0 Client ID")
                print(f"3. Descarga el JSON")
                print(f"4. Guárdalo como: {CREDENTIALS_FILE}")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guardar token
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


def create_folder(service, folder_name, parent_id=None):
    """Crea carpeta en Drive."""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()
    
    return folder.get('id')


def upload_file(service, file_path, folder_id=None):
    """Sube archivo a Drive con barra de progreso."""
    from tqdm import tqdm
    
    print(f"\n📤 Subiendo: {file_path.name}")
    print(f"   Tamaño: {file_path.stat().st_size / (1024**3):.2f} GB")
    
    file_metadata = {'name': file_path.name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(
        str(file_path),
        mimetype='application/zip',
        resumable=True,
        chunksize=50 * 1024 * 1024  # 50 MB chunks
    )
    
    request = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id,name,webViewLink'
    )
    
    # Upload con progreso
    response = None
    pbar = tqdm(total=100, desc="Subiendo", unit="%")
    
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            pbar.update(progress - pbar.n)
    
    pbar.close()
    
    return response


def main():
    print("=" * 60)
    print("📤 SUBIR DATASET A GOOGLE DRIVE")
    print("=" * 60)
    
    # Verificar que existe el archivo
    if not DATASET_ZIP.exists():
        print(f"❌ Dataset no encontrado: {DATASET_ZIP}")
        print("\nEjecuta primero:")
        print("  python ml/datasets/scripts/export_for_colab.py")
        sys.exit(1)
    
    print(f"\n✅ Dataset encontrado:")
    print(f"   {DATASET_ZIP}")
    print(f"   Tamaño: {DATASET_ZIP.stat().st_size / (1024**3):.2f} GB")
    
    # Autenticar
    print("\n🔐 Autenticando con Google Drive...")
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    print("✅ Autenticado")
    
    # Crear carpeta SIRCCD_Dataset
    print("\n📁 Creando carpeta SIRCCD_Dataset...")
    folder_id = create_folder(service, 'SIRCCD_Dataset')
    print(f"✅ Carpeta creada (ID: {folder_id})")
    
    # Subir archivo
    print("\n📤 Iniciando subida...")
    result = upload_file(service, DATASET_ZIP, folder_id)
    
    # Mostrar resultado
    print("\n" + "=" * 60)
    print("✅ SUBIDA COMPLETADA")
    print("=" * 60)
    print(f"\nArchivo: {result['name']}")
    print(f"ID: {result['id']}")
    print(f"Link: {result.get('webViewLink', 'N/A')}")
    print("\n📋 Próximos pasos:")
    print("1. Abre Google Colab: https://colab.research.google.com")
    print("2. Sube el notebook: ml/notebooks/SIRCCD_Training_Colab.ipynb")
    print("3. Ejecuta las celdas secuencialmente")
    print("=" * 60)


if __name__ == '__main__':
    main()
