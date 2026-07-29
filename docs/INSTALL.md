# Installing the site

## Requirements
- **MariaDB**
- **uv** ([Installation Guide](https://docs.astral.sh/uv/getting-started/installation))
- **Node.js** ([Download Link](https://nodejs.org/en/download))

## Setting up database
Install MariaDB
```sh
$ apt update
$ apt install mariadb-server libmysqlclient-dev
```

Create database and user
```sh
$ sudo mysql
```

```sql
DROP DATABASE IF EXISTS hwoj;
CREATE DATABASE hwoj DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;
GRANT ALL PRIVILEGES ON hwoj.* TO 'hwoj'@'localhost' IDENTIFIED BY '<mariadb user password>';
exit
```

### Other useful database commands
```sql
-- List of Databases
SHOW DATABASES WHERE `Database` NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys');
-- List of users
SELECT User, Host FROM mysql.global_priv;

mariadb-dump -u hwoj -p hwoj > backup_hwoj.sql -- Backup
mariadb -u hwoj -p hwoj < backup_hwoj.sql -- Restore

DROP DATABASE IF EXISTS hwoj; -- Delete databases
```

## Setting up backend
```sh
$ cd backend
$ uv sync
$ cp example.env .env        # Edit .env with your database credentials and secret key
```

Run test
```sh
$ uv run fastapi dev --port 8000 # For development only
```

## Setting up frontend
```sh
$ cd frontend
$ npm i
$ npm run build
```

Run test
```sh
$ npm run dev   # Development mode
```

## Setting up judge
```sh
$ cd judge
$ uv sync
$ cp example.env .env        # Edit .env with your Redis URL
```
See [JUDGE.md](JUDGE.md) for detailed judge setup including isolate sandbox and Docker.

## Setting up supervisord

Install supervisor:
```sh
$ apt install supervisor
```

Copy configs and fix paths:
```sh
$ cp configs/hwoj-backend.conf /etc/supervisor/conf.d/
$ cp configs/hwoj-judge.conf /etc/supervisor/conf.d/
# Edit /etc/supervisor/conf.d/*.conf — replace /home/oj/HWOJ with your deploy path
```

Make sure each service has its `.env` file in place, then start:
```sh
$ supervisorctl reread
$ supervisorctl update
$ supervisorctl start all
```

Check status:
```sh
$ supervisorctl status
```

## Setting up nginx
> **Nginx Setup:** Copy `/configs/nginx.conf`, change the <dist_folder> to your frontend `dist` folder, and configure `proxy_pass` to point to your FastAPI server (`http://127.0.0.1:8000`).