import re
import click
import pandas as pd

from workers.orm_core.model_operation import ModelingCRUD


@click.command()
# @click.option('--filepath', '-f', required=True)
@click.option('--task_id', '-tid', required=True)
def regex_checker(task_id):
    # try:
    #     df = pd.read_csv(filepath, encoding='utf-8')
    # except Exception as e:
    #     click.echo(e)
    #     return
    # error_dict = {}
    # for idx, row in df.iterrows():
    #     content = row['content']
    #     try:
    #         if not content:
    #             click.echo(f"There is no content in index {idx}")
    #         # content = content if isinstance(content, str) else str(content)
    #         re.compile(content)
    #     except re.error:
    #         error_dict.update({idx: content})
    #         continue
    # if not error_dict:
    #     click.echo(f"There is no invalid rules in file {filepath}")
    #     return
    # else:
    #     for key, value in error_dict.items():
    #         click.echo(f"idx: {key}\tcontent: {value}")

    worker = ModelingCRUD()

    rule_set = worker.session.query(worker.mr).filter(worker.mr.task_id == task_id).all()

    error_dict = {}
    for idx, rule in enumerate(rule_set):
        try:
            if not rule.content:
                click.echo(f"There is no content in index {idx}")
            re.compile(rule.content)
        except re.error:
            error_dict.update({idx: rule.content})
            continue

    if not error_dict:
        click.echo(f"There is no invalid rules in {task_id}")
        return
    else:
        for key, value in error_dict.items():
            click.echo(f"idx: {key}\tcontent: {value}")

    worker.dispose()


if __name__ == '__main__':
    regex_checker()
