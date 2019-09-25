import time
import requests
import pytz

from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from celery.task import task
from parse_rest.connection import register
from parse_rest.datatypes import Object

from temba.utils import json
from temba.utils.dates import str_to_datetime
from temba.utils.celery import nonoverlapping_task
from temba.utils.email import send_template_email

from .models import CreditAlert, Invitation, Org, TopUpCredits


@task(track_started=True, name="send_invitation_email_task")
def send_invitation_email_task(invitation_id):
    invitation = Invitation.objects.get(pk=invitation_id)
    invitation.send_email()


@task(track_started=True, name="send_alert_email_task")
def send_alert_email_task(alert_id):
    alert = CreditAlert.objects.get(pk=alert_id)
    alert.send_email()


@task(track_started=True, name="check_credits_task")
def check_credits_task():  # pragma: needs cover
    CreditAlert.check_org_credits()


@task(track_started=True, name="apply_topups_task")
def apply_topups_task(org_id):
    org = Org.objects.get(id=org_id)
    org.apply_topups()
    org.trigger_send()


@nonoverlapping_task(track_started=True, name="squash_topupcredits", lock_key="squash_topupcredits", lock_timeout=7200)
def squash_topupcredits():
    TopUpCredits.squash()


@task(track_started=True, name="import_data_to_parse")
def import_data_to_parse(
    branding,
    user_email,
    iterator,
    parse_url,
    parse_headers,
    collection,
    collection_type,
    collection_real_name,
    filename,
    needed_create_header,
    tz,
    dayfirst,
):  # pragma: needs cover
    start = time.time()
    load_len = len(iterator) - 1

    print(f"Started task to import {str(load_len)} row(s) to Parse")

    parse_batch_url = f"{settings.PARSE_URL}/batch"
    register(settings.PARSE_APP_ID, settings.PARSE_REST_KEY, master=settings.PARSE_MASTER_KEY)

    tz = pytz.timezone(tz)

    new_fields = {}
    fields_map = {}

    failures = []
    success = 0

    batch_size = 500
    batch_package = []
    batch_counter = 0
    order = 1

    for i, row in enumerate(iterator):
        if i == 0:
            counter = 0
            for item in row:
                if str(item).startswith("numeric_"):
                    field_type = "Number"
                    item = item.replace("numeric_", "")
                elif str(item).startswith("date_"):
                    field_type = "Date"
                    item = item.replace("date_", "")
                else:
                    field_type = "String"

                new_key = str(slugify(item)).replace("-", "_")
                new_fields[new_key] = dict(type=field_type)

                fields_map[counter] = dict(name=new_key, type=field_type)
                counter += 1

            if needed_create_header:
                add_new_fields = {"className": collection, "fields": new_fields}
                requests.put(parse_url, data=json.dumps(add_new_fields), headers=parse_headers)
        else:
            payload = dict()
            for item in list(fields_map.keys()):
                try:
                    field_value = row[item]

                    if fields_map[item].get("type") == "Number":
                        field_value = float(field_value)
                    elif fields_map[item].get("type") == "Date":
                        field_value = field_value.replace("-", "/")
                        try:
                            field_value = str_to_datetime(
                                date_str=field_value, tz=tz, dayfirst=dayfirst, fill_time=False
                            )
                        except Exception:
                            field_value = None
                    else:
                        field_value = str(field_value).strip()

                    payload[fields_map[item].get("name")] = field_value
                except Exception:
                    if str(i) not in failures:
                        failures.append(str(i))

            payload["order"] = order
            real_collection = Object.factory(collection)
            new_item = real_collection(**payload)
            batch_package.append(new_item)
            batch_counter += 1
            order += 1

        if batch_counter >= batch_size:
            methods = list([m.save for m in batch_package])
            if not methods:
                return
            queries, callbacks = list(zip(*[m(batch=True) for m in methods]))
            response = requests.post(parse_batch_url, data=json.dumps(dict(requests=queries)), headers=parse_headers)
            if response.status_code == 200:
                for item in response.json():
                    if "success" in item:
                        success += 1
                    else:
                        failures.append(item.get("error"))
            batch_package = []
            batch_counter = 0

    # commit any remaining objects
    if batch_package:
        methods = list([m.save for m in batch_package])
        if not methods:
            return
        queries, callbacks = list(zip(*[m(batch=True) for m in methods]))
        response = requests.post(parse_batch_url, data=json.dumps(dict(requests=queries)), headers=parse_headers)
        if response.status_code == 200:
            for item in response.json():
                if "success" in item:
                    success += 1
                else:
                    failures.append(item.get("error"))

    print("-- Importation task ran in %0.2f seconds" % (time.time() - start))

    subject = _(f"Your {collection_type} Upload to Community Connect is Complete")
    template = "orgs/email/importation_email"

    failures = ", ".join(failures) if failures else None

    context = dict(
        now=timezone.now(),
        subject=subject,
        success=success,
        failures=failures,
        collection_real_name=collection_real_name,
        collection_type=collection_type,
        filename=filename,
    )

    send_template_email(user_email, subject, template, context, branding)
