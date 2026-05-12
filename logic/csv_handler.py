import csv
import io
from db import database as db

CSV_COLUMNS = [
    'display_id', 'parent_display_id', 'title', 'description',
    'type', 'priority', 'status', 'source', 'author', 'created_at'
]

VALID_TYPES = ['бизнес', 'пользовательское', 'функциональное', 'нефункциональное']
VALID_PRIORITIES = ['высокий', 'средний', 'низкий']
VALID_STATUSES = ['черновик', 'на рассмотрении', 'утверждено', 'реализовано', 'проверено']


def export_to_csv(project_id: int, filters: dict = None) -> str:
    reqs = db.get_requirements(project_id, filters)
    req_map = {r['id']: r for r in reqs}
    parent_map = {r['id']: r['display_id'] for r in reqs}

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, lineterminator='\n')
    writer.writeheader()

    for r in reqs:
        parent_did = ''
        if r['parent_id']:
            parent_row = db.get_requirement(r['parent_id'])
            if parent_row:
                parent_did = parent_row['display_id']
        writer.writerow({
            'display_id': r['display_id'],
            'parent_display_id': parent_did,
            'title': r['title'],
            'description': r['description'] or '',
            'type': r['type'],
            'priority': r['priority'],
            'status': r['status'],
            'source': r['source'] or '',
            'author': r['author_name'] or '',
            'created_at': r['created_at'],
        })
    return output.getvalue()


def import_from_csv(project_id: int, csv_content: str, author_id: int) -> dict:
    reader = csv.DictReader(io.StringIO(csv_content))
    errors = []
    created = 0
    skipped = 0

    # Check required columns
    required = {'title'}
    if not required.issubset(set(reader.fieldnames or [])):
        return {'created': 0, 'skipped': 0, 'errors': ['Отсутствует обязательный столбец: title']}

    rows = list(reader)
    # First pass: create root requirements
    display_id_map = {}
    for i, row in enumerate(rows, start=2):
        title = row.get('title', '').strip()
        if not title:
            errors.append(f"Строка {i}: пустое название — пропущено")
            skipped += 1
            continue

        parent_did = row.get('parent_display_id', '').strip()
        req_type = row.get('type', 'функциональное').strip()
        priority = row.get('priority', 'средний').strip()
        status = row.get('status', 'черновик').strip()
        source = row.get('source', '').strip()
        description = row.get('description', '').strip()

        if req_type not in VALID_TYPES:
            req_type = 'функциональное'
        if priority not in VALID_PRIORITIES:
            priority = 'средний'
        if status not in VALID_STATUSES:
            status = 'черновик'

        if parent_did:
            # Defer to second pass
            display_id_map[row.get('display_id', '')] = {
                'parent_did': parent_did, 'title': title,
                'description': description, 'type': req_type,
                'priority': priority, 'status': status, 'source': source,
            }
            continue

        try:
            req_id = db.create_requirement(
                project_id, None, title, description,
                req_type, priority, status, source, author_id
            )
            raw_did = row.get('display_id', '').strip()
            if raw_did:
                display_id_map[raw_did] = req_id
            created += 1
        except Exception as e:
            errors.append(f"Строка {i}: {e}")
            skipped += 1

    # Second pass: create sub-requirements
    for raw_did, data in list(display_id_map.items()):
        if not isinstance(data, dict):
            continue
        parent_did = data['parent_did']
        # Find parent id by display_id in DB
        all_reqs = db.get_requirements(project_id)
        parent_req = next((r for r in all_reqs if r['display_id'] == parent_did), None)
        parent_id = parent_req['id'] if parent_req else None

        try:
            db.create_requirement(
                project_id, parent_id, data['title'], data['description'],
                data['type'], data['priority'], data['status'], data['source'], author_id
            )
            created += 1
        except Exception as e:
            errors.append(f"Подтребование '{raw_did}': {e}")
            skipped += 1

    return {'created': created, 'skipped': skipped, 'errors': errors}
