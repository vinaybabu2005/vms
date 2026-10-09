# Update your existing Render site

1. Open github.com/vinaybabu2005/vms and enter its **vms_store** folder.
2. Click Add file -> Upload files.
3. From the upgraded local vms_store folder, drag these folders and files into the upload area:
   - config/
   - store/
   - templates/
   - static/
   - requirements.txt
   - build.sh
   - start.sh
   - README.md
4. Keep their folders intact. Do NOT upload venv/, .venv/, staticfiles/, db.sqlite3 or database.sql as part of the code update. Do NOT create a second vms_store folder inside the existing one. Commit the changes to main. The upload includes the new migrations.
5. Render -> your existing service -> Settings:
   Root Directory: vms_store
   Build Command: bash build.sh
   Start Command: bash start.sh
6. Render -> Environment: retain your private VMS_ADMIN_PASSWORD. Set VMS_ADMIN_USERNAME to vms (or your desired staff username). Add DJANGO_SECRET_KEY with a private long random value, and DJANGO_DEBUG with value 0. Do not put passwords on GitHub.
7. Manual Deploy -> Deploy latest commit. Wait for Live.
8. Open your site. Click Admin Login. Use VMS_ADMIN_USERNAME (default vms) and your private VMS_ADMIN_PASSWORD. The dashboard is /dashboard/.

Keep environment variables private. Bootstrap sets the environment admin password at each start. Existing local passwords are unchanged.

Storage: the old SQLite deployment uses temporary local storage. New orders/users/uploads can disappear on restart or deployment. Code updates do not fix this; persistent database and image storage must be configured for permanent store data. This project supports DATABASE_URL for PostgreSQL or VMS_DATA_DIR for an attached persistent disk; switching storage requires migrating existing data. See README.
