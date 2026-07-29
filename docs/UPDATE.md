# Updating the site

Pull the latest changes
```sh
$ git pull origin master
```

## Updating backend / database

Backend's latest changes:
```sh
$ cd backend
$ uv sync # install any missing libraries
```

Database schemas update using `alembic`:
```sh
$ uv run alembic upgrade head
```

If you make any changes related to database schemas, this command creates a version upgrade for `alembic`:
```sh
$ uv run alembic revision --autogenerate -m "<message>"
```

## Update frontend
```sh
$ cd frontend
$ npm i # install any missing packages
$ npm run build # and rebuild
```

## Update discordbot
```sh
$ cd discordbot
$ uv sync # install any missing libraries
```
