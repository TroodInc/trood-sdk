import os
from time import strftime, gmtime

import click
import zipfile
import requests

from pyfiglet import Figlet
from trood.cli import utils


@click.group()
def trood():
    pass


@trood.command()
def info():
    f = Figlet(font='slant')
    click.echo(f.renderText('TROOD'), nl=False)
    click.echo('Welcome to Trood sdk! Use `trood --help` to view all commands.')
    click.echo()


@trood.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def login(username: str, password: str):
    result = requests.post(
        'https://tcp.trood.com/auth/api/v1.0/login',
        json={'login': username.strip(), 'password': password.strip()}
    )

    if result.status_code == 200:
        data = result.json()
        utils.save_token(data["data"]["token"])

        click.echo(f'Successfully logged in as {username}')
    elif result.status_code == 403:

        click.echo(f'Login failed. Wrong login or password')
    else:

        click.echo(f'Cant login. Login server response: {result.json()}')


@trood.command()
def logout():
    click.confirm('Do you want to logout ?', abort=True)

    requests.post('https://tcp.trood.com/auth/api/v1.0/logout', headers={"Authorization": utils.get_token()})

    utils.clean_token()


@trood.group()
def space():
    pass


@space.command()
def ls():
    result = requests.get(
        "http://em.tools.trood.ru/api/v1.0/spaces/",
        headers={"Authorization": utils.get_token()}
    )

    if result.status_code == 200:
        utils.list_table(result.json())


@space.command()
@click.argument('space_id')
def rm(space_id):
    click.confirm(f'Do you want to remove space #{space_id} ?', abort=True)
    result = requests.delete(
        f'http://em.tools.trood.ru/api/v1.0/spaces/{space_id}/',
        headers={"Authorization": utils.get_token()}
    )

    if result.status_code == 204:
        click.echo(f'Space #{space_id} removed successfully!')


@space.command()
@click.argument('name')
def create(name):
    result = requests.post(
        f'http://em.tools.trood.ru/api/v1.0/spaces/',
        headers={"Authorization": utils.get_token()},
        json={'name': name}
    )

    if result.status_code == 201:
        click.echo(f'Space {name} created successfully!')


@space.command()
@click.argument('space_id')
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def publish(space_id, path):
    click.confirm(f'Do you want to publish "{path}" to yout space #{space_id}?', abort=True)

    def zipdir(path, ziph):
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                fp = os.path.join(root, file)
                zp = fp.replace(path, '')

                ziph.write(filename=fp, arcname=zp)

    time = strftime("%Y-%m-%d__%H-%M-%S", gmtime())

    zipf = zipfile.ZipFile(f'{space_id}-{time}.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir(path, zipf)
    zipf.close()

    result = requests.post(
        f'http://em.tools.trood.ru/api/v1.0/spaces/{space_id}/publish/',
        headers={"Authorization": utils.get_token()},
        files={'bundle': open(f'{space_id}-{time}.zip', 'rb')}
    )

    if result.status_code == 201:
        click.echo(f'Web app successfuly published to http://{space_id}.saas.trood.ru')
    else:
        click.echo(f'Error while publishing: {result.content}', err=True)
