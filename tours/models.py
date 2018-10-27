import csv

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms.models import model_to_dict
from pytils.numeral import choose_plural


class BaseCatalog(models.Model):
    """Базовая абстрактная модель, представляющая набор полей для справочников."""
    name = models.CharField(max_length=150, db_index=True, default='', verbose_name='Название Ru')
    name_en = models.CharField(max_length=150, blank=True, default='', verbose_name='Название En')
    description = models.CharField(max_length=500, blank=True, default='', verbose_name='Описание')

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class TripType(BaseCatalog):
    show_on_main_page = models.BooleanField(default=False, db_index=True,
                                            verbose_name='Отображать на главной')
    is_active = models.BooleanField(default=False, db_index=True, verbose_name='Активен')
    ordering = models.FloatField(db_index=True, default=1.0, verbose_name='Приоритет расположения')
    highlight = models.BooleanField(default=False, verbose_name='Подсвечивать')
    is_hot = models.BooleanField(default=False, verbose_name='Горящий тур')
    hot_tour_link = models.TextField(verbose_name='Ссылка на витрину горящих туров',
                                     blank=True, null=True)

    class Meta:
        verbose_name = 'Тип отдыха'
        verbose_name_plural = 'Типы отдыха'

    def as_dict(self):
        result = model_to_dict(self)
        result['pk'] = self.id
        return result


class Provider(BaseCatalog):
    class Meta:
        verbose_name = 'Поставщик тура'
        verbose_name_plural = 'Поставщики тура'


class Service(BaseCatalog):
    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'


class RoomType(BaseCatalog):
    class Meta:
        verbose_name = 'Тип комнаты'
        verbose_name_plural = 'Типы комнат'


class BoardType(BaseCatalog):
    class Meta:
        verbose_name = 'Тип питания'
        verbose_name_plural = 'Типы питания'


class Tour(models.Model):

    class Type:
        RECREATION_TOUR = 1
        EVENT_TOUR = 2
        GOLD_TOUR = 3
        VIP_TOUR = 4

        choices = (
            (RECREATION_TOUR, 'Тур'),
            (EVENT_TOUR, 'Событие'),
            (GOLD_TOUR, 'Золотой тур'),
            (VIP_TOUR, 'VIP тур'),
        )

    class PriceType:
        PER_PERSON = 1
        PER_ROOM = 2

        choices = (
            (PER_PERSON, 'руб./чел.'),
            (PER_ROOM, 'руб.')
        )

    tour_type = models.PositiveSmallIntegerField(db_index=True, choices=Type.choices,
                                                 default=Type.RECREATION_TOUR,
                                                 verbose_name='Тип тура')
    title = models.CharField(max_length=150, blank=True, null=True, db_index=True, verbose_name='Название тура')
    trip_type = models.ForeignKey(TripType, blank=True, null=True, verbose_name='Тип отдыха', on_delete=models.CASCADE)
    text = models.TextField(blank=True, verbose_name='Полное описание')
    description = models.TextField(blank=True, verbose_name='Краткое описание')
    comment = models.TextField(blank=True, verbose_name='Отзыв')
    city = models.ForeignKey('offer.City', verbose_name='Город', on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, blank=True, null=True, verbose_name='Поставщик', on_delete=models.CASCADE)
    # Поле для EventTour
    tickets = models.PositiveSmallIntegerField(default=0, verbose_name='Билеты')
    priority = models.PositiveSmallIntegerField(default=0, db_index=True, verbose_name='Приоритет')
    products = ArrayField(
        models.CharField(max_length=32),
        verbose_name='Продукты',
        default=[]
    )
    is_best_tour = models.BooleanField(default=False, verbose_name='Лучший тур')
    is_best_price = models.BooleanField(default=False, verbose_name='Лучшая цена')
    is_editors_choice = models.BooleanField(default=False, verbose_name='Выбор редакции')
    min_price = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=2,
                                    verbose_name='Стоимость, в рублях')
    price_type = models.PositiveSmallIntegerField(default=PriceType.PER_PERSON, choices=PriceType.choices,
                                                  verbose_name='Тип цены')
    user_updated = models.ForeignKey(User, blank=True, null=True,
                                     verbose_name='Изменено пользователем',
                                     on_delete=models.CASCADE)
    tags = models.ManyToManyField('core.Tag', blank=True, related_name='%(class)s_tags',
                                  verbose_name='Теги')

    # даты тура и длительность
    begins_at = models.DateField(blank=True, null=True, verbose_name='Дата начала')
    ends_at = models.DateField(blank=True, null=True, verbose_name='Дата окончания')
    duration_days = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Продолжительность в днях')
    duration_nights = models.PositiveSmallIntegerField(verbose_name='Продолжительность в ночах')

    # перелет
    is_flight_included = models.BooleanField(default=False, verbose_name='Перелет включен')
    airline = models.CharField(blank=True, max_length=100, verbose_name='Авиакомпания')
    airport_departure = models.CharField(blank=True, max_length=100,
                                         verbose_name='Аэропорт вылета')
    airport_arrival = models.CharField(blank=True, max_length=100, verbose_name='Аэропорт прилета')
    departure_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата и время вылета')
    arrival_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата и время прилета')
    transit_flight = models.BooleanField(default=False, verbose_name='Пересадка')
    transit_airport_arrival = models.CharField(blank=True, max_length=100,
                                               verbose_name='Аэропорт прилета (пересадка)')
    transit_arrival_at = models.DateTimeField(blank=True, null=True,
                                              verbose_name='Дата и время прилета (пересадка)')
    transit_airport_departure = models.CharField(blank=True, max_length=100,
                                                 verbose_name='Аэропорт вылета (пересадка)')
    transit_departure_at = models.DateTimeField(blank=True, null=True,
                                                verbose_name='Дата и время вылета (пересадка)')
    # трансфер
    is_transfer_included = models.BooleanField(default=False, verbose_name='Трансфер включен')
    transfer_description = models.TextField(blank=True, verbose_name='Описание трансфера')

    # страховка
    is_insurance_included = models.BooleanField(default=False, verbose_name='Страховка включена')
    insurance_description = models.TextField(blank=True, verbose_name='Описание страховки')

    # обложка тура
    cover = models.ForeignKey('images.OriginalImage', null=True, blank=True, related_name='tours',
                              verbose_name='Обложка', on_delete=models.CASCADE)
    datetime_cover = models.DateTimeField(blank=True, null=True,
                                          verbose_name='Дата создания/редактирования обложки')
    photos = models.ManyToManyField('images.OriginalImage', blank=True, verbose_name='Фотографии')
    services = models.ManyToManyField(Service, blank=True, verbose_name='Услуги')

    class Meta:
        verbose_name = 'Тур'
        verbose_name_plural = 'Туры'

    def __str__(self):
        return '{id} - {title}'.format(id=self.id, title=self.title)

    def slug(self):
        return '/tours/{id}/'.format(id=self.id)

    @property
    def is_per_person(self):
        return self.price_type == self.PriceType.PER_PERSON

    @property
    def country(self):
        return self.city.country.name

    @property
    def hotel(self):
        """Возвращает первый связанный отель.

        Для рекреационных туров данный отель должен являться единственным.
        Данный метод с использованием индекса queryset является наиболее оптимальным,
        т.к. при возврате множества туров зараннее полученые методом prefetch_related отели
        не порождают новых запросов к БД при получении конкретного отеля у конкретного тура.
        """
        try:
            hotel = self.hotels.all()[0]
        except IndexError:
            hotel = None
        return hotel

    @property
    def services_list(self):
        services = [service.name for service in self.services.all()]
        if self.is_transfer_included:
            services.append('Трансфер')
        if self.is_insurance_included:
            services.append('Страховка')
        if self.is_flight_included:
            services.append('Авиаперелет')
        return services

    def format_tour_durations(self):
        """Получает продолжительность тура в формате "X дней / Y ночей"."""
        days = self.duration_days or 0
        nights = self.duration_nights or 0
        tour_durations = '{days_num} {days_str} / {nights_num} {nights_str}'.format(
            days_num=days,
            nights_num=nights,
            days_str='д' + choose_plural(days, 'ень,ня,ней'),
            nights_str='ноч' + choose_plural(nights, 'ь,и,ей')
        )
        return tour_durations

    def get_tour_info(self, br_line_breaks=False):
        tour_info = ['{}, {}'.format(self.city.country.name, self.title)]

        if self.description:
            tour_info.append(self.description)

        if self.begins_at or self.ends_at:
            dates_info = 'Даты:'
            if self.begins_at:
                dates_info += ' с {}'.format(self.begins_at.strftime('%d.%m.%Y'))
            if self.ends_at:
                dates_info += ' по {}'.format(self.ends_at.strftime('%d.%m.%Y'))
            tour_info.append(dates_info)

        tour_info.append('Продолжительность тура ' + self.format_tour_durations())
        tour_info.append('Стоимость {} руб.'.format(self.min_price))

        if self.hotel:
            if self.hotel.accommodation:
                if self.hotel.accommodation.food:
                    tour_info.append('Тип питания {}'.format(self.hotel.accommodation.food.name))

        if (self.services.exists() or self.is_transfer_included or self.is_insurance_included or
                self.is_flight_included):
            tour_info.append('В тур включены {}'.format(', '.join(self.services_list)))

        linebreak = '<br />' if br_line_breaks else '\n'
        return linebreak.join(tour_info)

    @property
    def special(self):
        return self.tour_type > 2

    @classmethod
    def export_to_csv(cls, file_obj, tours_qs):
        """Производит выгрузку выбранных туров в csv-файл.

        :param file_obj: File-like объект, в который будет записана выгрузка.
        :param tours_qs: Экспортируемые туры (их выборка).
        """
        tours_qs = tours_qs.select_related('trip_type', 'city', 'city__country')
        dump_writer = csv.DictWriter(file_obj, fieldnames=['Type', 'City', 'Country'], dialect=csv.excel)
        dump_writer.writeheader()
        for tour_num, tour_obj in enumerate(tours_qs, start=1):
            dump_data = [
                tour_num,
                tour_obj.pk,
                tour_obj.get_absolute_url(),
                str(tour_obj.trip_type),
                str(tour_obj.city.country) if tour_obj.city is not None else '',
                str(tour_obj.city),
                tour_obj.title,
                tour_obj.hotel.category if tour_obj.hotel is not None else '',
                tour_obj.min_price,
                tour_obj.format_tour_durations(),
                tour_obj.begins_at,
                tour_obj.ends_at,
            ]
            row = dict(zip(['Title', 'Value'], dump_data))
            dump_writer.writerow(row)

