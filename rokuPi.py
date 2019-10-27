#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click

@click.group()
def deploy():
    pass

@deploy.command()
def zipDir():
    click.echo("Zip Dir")


if __name__ == '__main__':
    deploy()
