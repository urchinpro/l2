import datetime

import requests
from django.core.management import BaseCommand
from django.db.models import Q
from django.utils.timezone import now
from requests import Session
from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder
from zeep.transports import Transport
from zeep import Client
from time import strftime, gmtime, localtime
from appconf.manager import SettingManager
from directions.models import Issledovaniya, Result
from django.test import Client as TC

import simplejson as json


class Command(BaseCommand):
    help = "Выгрузка результатов в РМИС"

    def handle(self, *args, **options):

        orgname = "Клиники ФГБОУ ВО ИГМУ Минздрава России"
        directory = SettingManager.get("rmis_path_directory")
        patients = SettingManager.get("rmis_path_patients")
        directions = SettingManager.get("rmis_path_directions")
        services = SettingManager.get("rmis_path_services")
        medservices = SettingManager.get("rmis_path_medservices")
        orgs_table = "pim_organization"
        orgs_code = ""
        dep_table = "pim_department"
        dep_code = ""
        docs_table = "pc_doc_type"
        docs_code = ""
        polis_ids = []
        dir_types_table = "md_referral_type"
        dir_types_code = ""
        dir_type_lab_id = ""
        lab_title = SettingManager.get("rmis_lab_title")
        lab_id = ""
        celi_table = "md_referral_goal"
        celi_code = ""
        cel_id = ""
        service_table = "fer_se_service_type"
        service_code = ""
        login = SettingManager.get("rmis_login")
        passw = SettingManager.get("rmis_password")
        rmis_address = SettingManager.get("rmis_address")
        upload_after = SettingManager.get("rmis_upload_results_after")
        session = Session()
        session.auth = HTTPBasicAuth(login, passw)

        def gclient(addr):
            return Client(f"{rmis_address}{addr}", transport=Transport(session=session))

        clientDirectory = gclient(directory)

        rb = clientDirectory.service.getRefbookList()
        for rowN in rb:
            row = rowN["column"]
            code = ""
            table = ""
            for col in row:
                if col["name"] == "CODE":
                    code = col["data"]
                if col["name"] == "TABLE_NAME":
                    table = col["data"]
            if table == orgs_table:
                orgs_code = code
            if table == docs_table:
                docs_code = code
            if table == dir_types_table:
                dir_types_code = code
            if table == dep_table:
                dep_code = code
            if table == celi_table:
                celi_code = code
            if table == service_table:
                service_code = code

        self.stdout.write(orgs_table + " " + orgs_code)
        self.stdout.write(docs_table + " " + docs_code)
        self.stdout.write(dir_types_table + " " + dir_types_code)
        rp = clientDirectory.service.getRefbookRowData(refbookCode=orgs_code, version="CURRENT",
                                                       column={"name": "FULL_NAME", "data": orgname})
        ORGID = rp[0]["column"][0]["data"]
        self.stdout.write(orgname + " ID: " + ORGID)

        rp = clientDirectory.service.getRefbookRowData(refbookCode=dep_code, version="CURRENT",
                                                       column={"name": "NAME", "data": lab_title})
        for r in rp:
            rr = r["column"]
            for rrr in rr:
                if rrr["name"] == "ORG_ID" and rrr["data"] == ORGID:
                    lab_id = rr[0]["data"]
                    break
            if lab_id != "":
                break

        self.stdout.write("lab_id" + " " + lab_id)

        rp = clientDirectory.service.getRefbookRowData(refbookCode=docs_code, version="CURRENT",
                                                       column={"name": "NAME", "data": "Полис"})
        polis_ids = [x["column"][0]["data"] for x in rp]
        self.stdout.write("polis_ids" + " " + str(polis_ids))

        rp = clientDirectory.service.getRefbookRowData(refbookCode=dir_types_code, version="CURRENT",
                                                       column={"name": "NAME", "data": "Направление в лабораторию"})
        dir_type_lab_id = rp[0]["column"][0]["data"]
        self.stdout.write("dir_type_lab_id" + " " + dir_type_lab_id)

        rp = clientDirectory.service.getRefbookRowData(refbookCode=celi_code, version="CURRENT",
                                                       column={"name": "NAME", "data": "Для коррекции лечения"})
        cel_id = rp[0]["column"][0]["data"]
        self.stdout.write("cel_id" + " " + cel_id)

        polis_cache = {}
        from directions.models import Napravleniya

        clientPatients = gclient(patients)
        clientDirections = gclient(directions)
        clientMedservices = gclient(medservices)

        date = datetime.date(int(upload_after.split(".")[2]), int(upload_after.split(".")[1]),
                             int(upload_after.split(".")[0])) - datetime.timedelta(minutes=20)

        c = TC(enforce_csrf_checks=False)
        cstatus = c.login(username="rmis", password="clientDirections.service.sendReferral")
        self.stdout.write("AUTH " + str(cstatus))
        for d in Napravleniya.objects.filter(issledovaniya__time_confirmation__gte=date).filter(
                        Q(rmis_number__isnull=True) | Q(rmis_number="")).distinct():
            polis_pk = f"{d.client.polis_serial}-{d.client.polis_number}"
            if polis_pk not in polis_cache:
                patinet_id = ""

                for p in polis_ids:
                    sp = clientPatients.service.searchIndividual(
                        searchDocument={"docTypeId": p, "docNumber": d.client.polis_number})
                    if len(sp) > 0:
                        patinet_id = sp[0]
                        break
                if patinet_id == "":
                    for p in polis_ids:
                        sp = clientPatients.service.searchIndividual(
                            searchDocument={"docTypeId": p, "docNumber": d.client.polis_number,
                                            "docSeries": d.client.polis_serial})
                        if len(sp) > 0:
                            patinet_id = sp[0]
                            break
                polis_cache[polis_pk] = patinet_id
                if patinet_id == "":
                    d.rmis_number = "NONERMIS"
                    d.save()
                self.stdout.write(f"{polis_pk} {'noneRMIS' if polis_cache[polis_pk] == '' else polis_cache[polis_pk]}")
            if polis_cache[polis_pk] == "":
                continue
            data = d.data_sozdaniya.strftime("%Y-%m-%d")
            services_tmp = [x.fraction.code.replace("А", "A").replace("В", "B") for x in
                            Result.objects.filter(issledovaniye__napravleniye=d) if x.fraction.code != ""]
            self.stdout.write(str(services_tmp))
            services_dict = {}
            stt = self
            clientServices = gclient(services)
            srv = clientServices.service.getServices(clinic=ORGID)
            for r in srv:
                services_dict[r["code"]] = r["id"]

            def get_service_id(s):
                if s in services_dict:
                    return services_dict[s]
                stt.stdout.write(f"NONE {s}")
                return None

            services_ids = [y for y in [get_service_id(x) for x in services_tmp] if y is not None]
            dates = {}

            direction_id = clientDirections.service.sendReferral(patientUid=patinet_id,
                                                                 number=str(d.pk),
                                                                 typeId=dir_type_lab_id,
                                                                 referralDate=data,
                                                                 referralOrganizationId=ORGID,
                                                                 referringDepartmentId=lab_id,
                                                                 receivingOrganizationId=ORGID,
                                                                 receivingDepartmentId=lab_id,
                                                                 refServiceId=services_ids,
                                                                 goalId=cel_id)
            d.rmis_number = direction_id
            d.save()
            stt.stdout.write(f"NEW DIRECTION {direction_id}")

            r = c.get("/directions/pdf", {"napr_id": json.dumps([d.pk])})
            self.stdout.write("STATUS GET NAPR PDF " + str(r.status_code))

            multipart_data = MultipartEncoder(
                fields={'file': ('direction.pdf', r.content, 'application/pdf')},

            )
            resip = requests.request("PUT",
                                     f"https://38.is-mis.ru/referral-attachments-ws/rs/referralAttachments/{direction_id}/Направление/direction.pdf",
                                     data=multipart_data,
                                     headers={'Content-Type': "multipart/form-data"}, auth=HTTPBasicAuth(login, passw))

            self.stdout.write("UPLOAD STATUS " + str(resip.status_code))

            r = c.get("/results/pdf", {"pk": json.dumps([d.pk])})
            self.stdout.write("STATUS GET RESULT PDF " + str(r.status_code))

            multipart_data = MultipartEncoder(
                fields={'file': ('result.pdf', r.content, 'application/pdf')},

            )
            resip = requests.request("PUT",
                                     f"https://38.is-mis.ru/referral-attachments-ws/rs/referralAttachments/{direction_id}/Результат/result.pdf",
                                     data=multipart_data,
                                     headers={'Content-Type': "multipart/form-data"}, auth=HTTPBasicAuth(login, passw))

            self.stdout.write("UPLOAD STATUS " + str(resip.status_code))

            for x in Result.objects.filter(issledovaniye__napravleniye=d):
                if x.fraction.code == "":
                    continue
                ssd = get_service_id(x.fraction.code)
                if ssd is None:
                    continue
                sid = clientMedservices.service.sendServiceRend(referralId=direction_id, serviceId=ssd,
                                                                isRendered="false",
                                                                patientUid=patinet_id, orgId=ORGID,
                                                                dateTo=x.issledovaniye.time_confirmation.strftime(
                                                                    "%Y-%m-%d"))
                self.stdout.write(f'SERVICE ADD {sid}')