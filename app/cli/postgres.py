import click

from os import environ
from sh import psql, createuser as pgcreateuser, dropuser as pgdropuser, createdb as pgcreatedb, dropdb as pgdropdb

try:
    from app.cli.utils import default_option
except ImportError:
    from utils import default_option

def create_user(name, pw):
    sql = "SELECT 1 FROM pg_roles WHERE rolname='%s'" % name
    if '1' in psql('-Upostgres', '-tAc', sql):
        click.echo("User already exists: " + name)
        return False

    click.echo("Creating user")
    psql('-Upostgres', "-c CREATE USER {} WITH PASSWORD '{}';".format(name, pw))
    return True

def create_db(name, owner):
    if name in psql('-Upostgres', '-lqtA'):
        click.echo("Database already exists: " + name)
        return False

    click.echo("Creating database")
    pgcreatedb('-Upostgres', '-O'+owner, name, encoding='utf-8')
    return True

def drop_db(name):
    pgdropdb('-Upostgres', name)

@click.group(help="postgres related commands")
def postgres():
    pass

@postgres.command(help="Creates postgres user")
@click.option('--user', default=default_option('DB_USER'))
@click.option('--password', default=default_option('DB_PASS'))
def createuser(user, password):
    click.echo("Creating user: "+user)
    return create_user(user, password)

@postgres.command(help=("Drops postgres user"))
@click.argument('name', default=default_option('DB_USER'))
def dropuser(user):
    click.echo("Dropping user: "+user)
    pgdropuser('-Upostgres', user)

@postgres.command(help="Creates database and extensions for app")
@click.option('--owner', default=default_option('DB_USER'))
@click.argument('name', default=default_option('DB_NAME'))
def initdb(name, owner):
    create_db(name, owner)
    psql('-Upostgres', "-d"+name, "-c CREATE EXTENSION IF NOT EXISTS postgis")

@postgres.command(help="Deletes database")
@click.argument('name', default=default_option('DB_NAME'))
def dropdb(name):
    click.echo("Dropping database: "+name)
    drop_db(name)

@postgres.command(help="Creates user and database")
@click.option('--user', default=default_option('DB_USER'))
@click.option('--password', default=default_option('DB_PASS'))
@click.option('--name', default=default_option('DB_NAME'))
@click.pass_context
def init(ctx, user, password, name):
    click.echo("init database")
    ctx.invoke(createuser, user=user, password=password)
    ctx.invoke(initdb, name=name, owner=user)

if __name__ == '__main__':
    postgres()
