import os
import click
import json
import requests

class FileMissingError(Exception):
    pass

@click.command()
@click.option('--file', required=True)
@click.option('--is_dev/--is_pro', default=False)
@click.option('--number_of_queue', default=4)
@click.option('--model_type', default='keyword_model')
@click.option('--predict_type', default='author_name')
@click.option('--year', default='2021')
def run_command(file, is_dev, number_of_queue, model_type, predict_type, year):

    if not os.path.isfile(file):
        raise FileMissingError(f'{file} does not exist in directory')

    with open(file, 'r') as f:
        requirement_list = f.read().split()

    if is_dev:
        api_path = 'http://127.0.0.1:8000/api/tasks/'
    else:
        api_path = 'http://0.0.0.0:8000/api/tasks/'

    api_headers = {
        'accept': 'application/json',
    }

    count = 1
    for i in requirement_list:

        api_request_body = {
          "MODEL_TYPE": f"{model_type}",
          "PREDICT_TYPE": f"{predict_type}",
          "START_TIME": f"{year}-01-01 00:00:00",
          "END_TIME": f"{int(year)+1}-01-01 00:00:00",
          "INPUT_SCHEMA": f"{i}",
          "INPUT_TABLE": "ts_page_content",
          "OUTPUT_SCHEMA": "audience_result",
          "COUNTDOWN": 5,
          "QUEUE": f"queue{count}"
        }
        if count < number_of_queue:
            count += 1
        else:
            count = 1

        # click.echo(api_request_body)

        r = requests.post(api_path, headers=api_headers, data=json.dumps(api_request_body))
        click.echo(r.status_code)
        click.echo(r.json())

if __name__ == '__main__':
    run_command()
