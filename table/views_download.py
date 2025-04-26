import os
from django.http import FileResponse, Http404
from django.conf import settings

def download_db(request, db_name):
    if db_name not in ['real.sqlite3', 'example.sqlite3']:
        raise Http404("Invalid database name.")

    file_path = os.path.join(settings.BASE_DIR, db_name)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=db_name)
    else:
        raise Http404("File not found.")
