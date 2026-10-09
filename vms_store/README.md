# V.M.S Professional Store
Django, SQL, HTML and CSS. Upgraded from your uploaded project; existing accounts, products, images and orders are retained in the included SQLite database.

## Run in Windows / VS Code
Extract the ZIP. Open **vms_store**, the folder containing manage.py, in VS Code.
Run one line at a time:
```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```
Open http://127.0.0.1:8000/ . Do not use Live Server.

## Login
Homepage has User Login and Admin Login. User Login is for customer accounts. Admin Login is for active staff accounts, and leads to /dashboard/.
Existing account passwords are unchanged. To create your own local admin:
```powershell
.\venv\Scripts\python.exe manage.py createsuperuser
```
To reset an existing local account:
```powershell
.\venv\Scripts\python.exe manage.py changepassword admin
```
Local and Render accounts are independent. No new public admin password is introduced.

## Dashboard
- Overview: order value excluding cancellations, delivered order value, counts, seven-day chart, order pipeline, low-stock watch, recent orders.
- Orders: search, status filter, detail view, shipping editor, customer cancellation with reason, and confirmed deletion.
- Products: search, add/edit/delete, category, price, stock, image uploads (5 MB limit).
- Categories: add categories; delete only empty categories.
- Customers: searchable customer list and customer order history.
- Sidebar, responsive tables, mobile layout, separate staff login, customer isolation.
- Classic /admin/ remains available for advanced user/permission management. Order status/deletion is controlled through /dashboard/ to keep stock consistent.

## Shipping and status workflow
Placed -> Processing or Shipped; Processing -> Shipped; Shipped -> Delivered. A customer can cancel a placed or processing order at My Orders → View Order → Cancel this order and must choose a reason; optional notes are visible to the admin. Cancellation restores stock once. The customer sees courier, tracking number/link, estimated arrival, and shipping notes entered by the admin.
Placed/Processing -> Cancelled restores inventory once. Cancelled and delivered statuses are terminal. Shipped orders cannot be cancelled through this workflow. Name, phone and address lock after shipping/cancellation. Courier, tracking ID/link, delivery date and public shipping notes appear on the customer's own order page. Notes are visible to the customer.
Deleting an active unshipped order returns stock. Deleting a previously cancelled order does not restore again. Deleting a shipped/delivered order does not return stock. Deletions permanently remove order history; there is a confirmation page. Legacy orders already cancelled before this upgrade are not automatically restocked.
All dashboard pages and writes require an active staff account. Mutations use POST and CSRF protection. Cancel/stock/delete operations are atomic.

## Render update (including free service)
Back up live data first. Upload/commit the code and migrations into your existing GitHub repository. Keep root directory **vms_store**.
Build Command:
```bash
bash build.sh
```
Start Command:
```bash
bash start.sh
```
Render Environment:
- VMS_ADMIN_USERNAME: vms (optional; default is vms)
- VMS_ADMIN_PASSWORD: your private strong password (never commit it)
- DJANGO_SECRET_KEY: a private long random value
- DJANGO_DEBUG: 0

Manual Deploy -> Deploy latest commit. Startup migrates the database and configures the staff account using the environment, so paid Shell is unnecessary. If VMS_ADMIN_PASSWORD is omitted, existing accounts are unchanged. When supplied, it is applied each start. Open your site -> Admin Login -> dashboard.
The existing hostname vms-3-ue41.onrender.com is retained; Render's assigned hostname is also accepted automatically. CSS and badge use WhiteNoise and collectstatic.

### Storage limitations
The bundled SQLite file is a local/demo database. On Render's default ephemeral filesystem, new orders, users, products and uploaded images can disappear after restart/redeploy. The startup admin account is recreated if its password environment variable remains set. For durable data, configure DATABASE_URL for a persistent PostgreSQL database and persistent product image storage. Alternatively a Render persistent disk can be configured through VMS_DATA_DIR (paid disks); existing data must be migrated/copied before switching. PostgreSQL migration creates tables but does not import your SQLite data automatically. No external database or storage account has been provisioned.
The small demo serves public product media through Django. For larger production sites use dedicated media storage/CDN. Do not place private files in media/.

## Tests / files
```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test
```
Screenshots in screenshots/ include the upgraded dashboard and shipping editor. database.sql is a SQLite export of the included database. migrations/0003 includes the shipping fields; 0004 adds cancellation reasons and timestamps. Do not delete an existing live database to update this project; apply the migrations.
