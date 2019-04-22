import click

from flask import current_app
from flask.cli import with_appcontext
from os import environ
from sh import psql, createuser as pgcreateuser, dropuser as pgdropuser, createdb as pgcreatedb, dropdb as pgdropdb

@click.group(help="postgres related commands")
def postgres():
    pass

@postgres.command(help="Creates postgres user")
@with_appcontext
def createuser():
    environ['PGUSER'] = "postgres"
    click.echo("Creating user")
    user = current_app.config['DB_USER']
    pw = current_app.config['DB_PASS']
    psql("-c CREATE USER {} WITH PASSWORD '{}';".format(user, pw))

@postgres.command(help=("Drops postgres user"))
@with_appcontext
def dropuser():
    environ['PGUSER'] = "postgres"
    click.echo("Dropping user")
    pgdropuser(current_app.config['DB_USER'])

@postgres.command(help="Creates database and extensions for app")
@with_appcontext
def initdb():
    click.echo("Creating database")
    owner = current_app.config['DB_USER']
    name = current_app.config['DB_NAME']
    pgcreatedb("-O"+owner, name, encoding='utf-8')

    click.echo("Creating extensions")
    psql("-d"+name, "-c CREATE EXTENSION postgis")

@postgres.command(help="Deletes database")
@with_appcontext
def dropdb():
    environ['PGUSER'] = "postgres"

    click.echo("Dropping database")
    pgdropdb(current_app.config['DB_NAME'])

@postgres.command(help="Creates user and database")
@click.pass_context
def init(ctx):
    ctx.invoke(createuser)
    ctx.invoke(initdb)