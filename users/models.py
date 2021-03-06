import uuid

from django.db import models
from django.contrib.auth.models import User
from podrazdeleniya.models import Podrazdeleniya


class Speciality(models.Model):
    SPEC_TYPES = (
        (0, 'Консультации'),
    )

    title = models.CharField(max_length=255, help_text='Название')
    hide = models.BooleanField(help_text='Скрытие')
    spec_type = models.SmallIntegerField(choices=SPEC_TYPES, help_text='Тип специальности', default=0)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'


class DoctorProfile(models.Model):
    """
    Профили врачей
    """
    labtypes = (
        (0, "Не из лаборатории"),
        (1, "Врач"),
        (2, "Лаборант"),
    )
    user = models.OneToOneField(User, null=True, blank=True, help_text='Ссылка на Django-аккаунт', on_delete=models.CASCADE)
    specialities = models.ManyToManyField(Speciality, blank=True, default=None, help_text='Специальности пользователя')
    fio = models.CharField(max_length=255, help_text='ФИО')
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text='Подразделение', db_index=True, on_delete=models.CASCADE)
    isLDAP_user = models.BooleanField(default=False, blank=True, help_text='Флаг, показывающий, что это импортированый из LDAP пользователь')
    labtype = models.IntegerField(choices=labtypes, default=0, blank=True, help_text='Категория профиля для лаборатории')
    login_id = models.UUIDField(null=True, default=None, blank=True, unique=True, help_text='Код авторизации')

    def get_login_id(self):
        if not self.login_id:
            self.login_id = uuid.uuid4()
            self.save()
        c = '{:X>5}'.format(self.pk) + self.login_id.hex[:5]
        return c

    def get_fio(self, dots=True):
        """
        Функция формирования фамилии и инициалов (Иванов И.И.)
        :param dots:
        :return:
        """
        def gfl(w: str, dots):
            w = w.strip()
            if not w.isdigit() and len(w) > 0:
                w = w[0] + ("." if dots else "")
            return w
        fio = self.fio.strip().replace("  ", " ").strip()
        fio_split = fio.split(" ")

        if len(fio_split) == 0:
            return self.user.username
        if len(fio_split) == 1:
            return fio

        if len(fio_split) > 3:
            fio_split = [fio_split[0], " ".join(fio_split[1:-2]), fio_split[-1]]

        return fio_split[0] + " " + gfl(fio_split[1], dots) + ("" if len(fio_split) == 2 else gfl(fio_split[2], dots))

    def is_member(self, groups: list) -> bool:
        """
        Проверка вхождения пользователя в группу
        :param groups: названия групп
        :return: bool, входит ли в указаную группу
        """
        return self.user.groups.filter(name__in=groups).exists()

    def has_group(self, group) -> bool:
        return self.is_member([group])

    def __str__(self):  # Получение фио при конвертации объекта DoctorProfile в строку
        if self.podrazdeleniye:
            return self.fio + ', ' + self.podrazdeleniye.title
        else:
            return self.fio

    class Meta:
        verbose_name = 'Профиль пользователя L2'
        verbose_name_plural = 'Профили пользователей L2'


class AssignmentTemplates(models.Model):
    title = models.CharField(max_length=40)
    doc = models.ForeignKey(DoctorProfile, null=True, blank=True, on_delete=models.CASCADE)
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, related_name='podr', on_delete=models.CASCADE)

    def __str__(self):
        return (self.title + " | Шаблон для ") + (("всех" if self.podrazdeleniye is None else str(self.podrazdeleniye)) if self.doc is None else str(self.doc))

    class Meta:
        verbose_name = 'Шаблон назначений'
        verbose_name_plural = 'Шаблоны назначений'


class AssignmentResearches(models.Model):
    template = models.ForeignKey(AssignmentTemplates, on_delete=models.CASCADE)
    research = models.ForeignKey('directory.Researches', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.template) + "  | " + str(self.research)

    class Meta:
        verbose_name = 'Исследование для шаблона назначений'
        verbose_name_plural = 'Исследования для шаблонов назначений'
