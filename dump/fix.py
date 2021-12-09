import click
import configparser
import os
import glob
from tqdm import tqdm


class PathNotFoundError(Exception):
    """file dir not found"""
    pass

class FileNotFoundError(Exception):
    """no file in dir"""
    pass

def load_dump_file(path:str, file_name: str, **connection) -> None:
    host = connection['host']
    port = int(connection['port'])
    user = connection['user']
    password = connection['password']
    schema = connection['schema']

    command = f"""
            mysql -u{user} -p{password} -h{host} -P{port} {schema} < unzip -p {path}{file_name} 
            """
    os.system(command)


def run_dump_flow(path: str, **connection):

    if not os.path.isdir(path):
        raise PathNotFoundError(f"parent path not found")

    file_list = glob.glob(path + "*.zip")
    if not file_list:
        raise FileNotFoundError(f"there is no matching files in the {path}")

    for file in tqdm(file_list):
        print(file)
        # try:
        #     load_dump_file(path, file, **connection)
        # except Exception as e:
        #     raise f"fail to restore the {file} since {e}"

@click.command()
@click.option('--path', required=True)
@click.option('--connection', required=True, default='dump/config.ini')
def execute_task(path,connection):
    config = configparser.ConfigParser()
    config.read(connection)
    connection_dict = dict(config['CONNECTION'])
    run_dump_flow(path, **connection_dict)

    click.echo(f'all files from {path} are restored to '
               f'{connection_dict["host"]}:{connection_dict["port"]}/'
               f'{connection_dict["schema"]}')

if __name__ == '__main__':
    execute_task()
    # python dump/fix.py --path /home/deeprd2/audience_production/2021_11_26


