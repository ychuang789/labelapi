import click
import os

import tests

@click.command()
@click.option('--module_folder', required=True, default='model')
@click.option('--module_file', required=True, default='test_model_creator')
@click.option('--module_class')
@click.option('--module_method')
def testing(module_folder, module_file, module_class, module_method):
    if not module_class and module_method:
        click.echo(f'should include module_class if you wanna test single method')
        return

    if not module_class:
        full_path = tests.__name__ + '.' + module_folder + '.' + module_file
    elif not module_method:
        full_path = tests.__name__ + '.' + module_folder + '.' + module_file + '.' + module_class
    else:
        full_path = tests.__name__ + '.' + module_folder + '.' + module_file + '.' + module_class + '.' + module_method

    click.echo(f'test {full_path}')
    command = f"python -m unittest {full_path}"
    os.system(command)


if __name__ == '__main__':
    testing()
