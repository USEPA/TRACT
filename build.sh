pyinstaller --noconfirm --onefile --console \
  --add-data "C:/Users/TBROWN02/repo/monexif/monexif/monexif_fields.yml;." \
  --add-data "C:/Users/TBROWN02/repo/monexif/version.txt;." \
  "C:/Users/TBROWN02/repo/monexif/monexif/monexif_tk.py"