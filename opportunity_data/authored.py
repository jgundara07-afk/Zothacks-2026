"""Validate explicit self-guided tasks; external records still require HTTPS."""
def is_general_task(row):
    return row.get('source') == 'onething' and row.get('kind') == 'General task' and isinstance(row.get('general_task'),dict)


def validate_task(row):
    task=row['general_task']
    if task.get('difficulty') not in {'Lazy','Easy','Medium','Hard','Challenging'}:
        raise ValueError('Invalid general task difficulty')
    if type(task.get('minutes')) is not int or not 0 < task['minutes'] <= 120:
        raise ValueError('Invalid general task effort')
    if not task.get('steps') or any(not isinstance(step,str) or not step.strip() for step in task['steps']):
        raise ValueError('General task needs actionable steps')
    if row.get('source_url') != 'urn:onething:general-task:'+row['source_id']:
        raise ValueError('General task identifier mismatch')
