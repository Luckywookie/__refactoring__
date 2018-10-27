from django.forms import model_to_dict
from django.http import JsonResponse
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from .models import Tour


class ToursPageView(APIView):
    fields = [
        'id', 'title', 'trip_type', 'tour_type', 'city', 'country', 'cover_id', 'photos',
        'description', 'comment', 'html', 'hotel', 'hotels', 'provider', 'tickets',
        'flight_info', 'is_transfer_included', 'transfer_description', 'begins_at', 'ends_at',
        'duration_days', 'duration_nights', 'is_insurance_included', 'services',
        'services_list', 'insurance_description', 'similar_tours', 'min_price', 'is_per_person',
        'priority', 'is_old_tour'
    ]

    def get(self, request, *args, **kwargs):
        """GET API для Json отдачи туров (/pages/tours/).

        Принимает GET параметры, которые позволяют управлять выдачей туров.

        :query tours_id: id туров через запятую без пробела
        :query max_price: ограничение выборки по цене
        :query limit: ограничение выборки по количеству записей
        :query shuffle: (1 или 0), default - 0,  перемешивает выборку в случайном порядке
        """

        tours = Tour.objects.filter(published=True, trip_type__is_active=True).select_related(
            'city', 'city__country', 'provider', 'trip_type',
        ).prefetch_related(
            'hotels', 'hotels__accommodations'
        )

        # tours_id
        tours_id = request.GET.get('tours_id')
        if tours_id is not None:
            ids = list(map(int, tours_id.split(',')))
            tours = tours.filter(id__in=ids)

        # max_price
        try:
            max_price = int(request.GET.get('max_price', 0))
        except ValueError:
            max_price = 0
        if max_price:
            tours = tours.filter(min_price__lte=max_price)

        # shuffle
        shuffle = request.GET.get('shuffle', '0')
        if shuffle == '1':
            tours = tours.order_by('?')

        # Limit
        try:
            limit = int(request.GET.get('limit', 0))
        except ValueError:
            limit = 0
        if limit:
            tours = tours[:limit]

        tours = [model_to_dict(t, self.fields) for t in tours]
        return JsonResponse({'tours': tours})


class SimilarTourListView(ListAPIView):
    """API списка похожих туров (/api/similar-tours/<id>/)"""
    pagination_class = None

    def get(self, request, *args, **kwargs):
        tour_id = kwargs['id']

        obj = Tour.objects.get(pk=tour_id)
        similar_tours = Tour.objects.public().filter(tour_type=obj.tour_type).exclude(id=obj.id)

        if obj.tour_type == Tour.Type.RECREATION_TOUR:
            similar_tours = similar_tours.filter(trip_type=obj.trip_type)

        similar_tours = similar_tours.order_by('?').select_related('city', 'city__country', 'trip_type')[:4]

        result = []

        for tour in similar_tours:
            services = []
            tour_hotel = tour.hotel

            if tour_hotel:
                services.append('отель')
            if tour.is_flight_included:
                services.append('авиабилет')
            if tour.is_transfer_included:
                services.append('трансфер')
            if tour.is_insurance_included:
                services.append('страховка')
            if tour.tickets:
                services.append('билет на мероприятие')

            result.append({
                'id': tour.id,
                'title': tour.title,
                'city': {
                    'id': tour.city.id,
                    'name': tour.city.name,
                },
                'country': tour.country,
                'cover_id': tour.cover_id,
                'hotel': {
                    'name': tour_hotel.name if tour_hotel else None,
                    'category': tour_hotel.category if tour_hotel else None,
                },
                'begins_at': tour.begins_at,
                'ends_at': tour.ends_at,
                'duration_days': tour.duration_days,
                'duration_nights': tour.duration_nights,
                'min_price': tour.min_price,
                'is_per_person': tour.is_per_person,
                'services': services,
                'trip_type': tour.trip_type.name,
                'is_best_price': tour.is_best_price,
                'is_best_tour': tour.is_best_tour,
                'is_editors_choice': tour.is_editors_choice,
            })

        return JsonResponse(result)
