import keyring
import click
from tabulate import tabulate


def save_token(token):
    keyring.set_password("trood/em", "active", token)


def get_token():
    token = keyring.get_password("trood/em", "active")
    if token:
        return f'Token: {token}'
    else:
        click.echo(f'You need to login first.')


def clean_token():
    keyring.delete_password("trood/em", "active")


def list_table(items):
    if len(items):
        headers = items[0].keys()

        data = [i.values() for i in items]

        click.echo(tabulate(data, headers=headers))
        click.echo()
    else:
        click.echo('----------------- nothing to show')
