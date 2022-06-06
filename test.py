import click
import os

import tests

@click.command()
@click.option('--dir', '-D', required=True, default='model')
@click.option('--file', '-F', required=True, default='test_model_creator')
@click.option('--class_', '-C')
@click.option('--method', '-M')
def testing(dir, file, class_, method):
    if not class_ and method:
        click.echo(f'should include module_class if you wanna test single method')
        return

    if not class_:
        full_path = tests.__name__ + '.' + dir + '.' + file
    elif not method:
        full_path = tests.__name__ + '.' + dir + '.' + file + '.' + class_
    else:
        full_path = tests.__name__ + '.' + dir + '.' + file + '.' + class_ + '.' + method

    click.echo(f'test {full_path}')
    command = f"python -m unittest {full_path}"
    os.system(command)


if __name__ == '__main__':
    testing()
